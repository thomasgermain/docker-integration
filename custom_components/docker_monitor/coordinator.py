"""Docker monitor coordinator."""
from datetime import datetime, timedelta, timezone
from functools import partial
import logging
import threading
from typing import Any

from docker import DockerClient
from docker.models.containers import Container

from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class DockerMonitorCoordinator(DataUpdateCoordinator):
    """Docker monitor coordinator."""

    def __init__(
        self, hass: HomeAssistant, url: str, update_interval: timedelta
    ) -> None:
        """Init."""

        debouncer = Debouncer(
            hass,
            _LOGGER,
            cooldown=5.0,
            immediate=True,
            function=self.async_refresh,
        )

        super().__init__(
            hass,
            _LOGGER,
            name="DockerMonitorCoordinator",
            update_interval=update_interval,
            update_method=self._refresh,
            request_refresh_debouncer=debouncer,
        )

        self._url: str = url
        self._docker: DockerClient
        self._containers: list[Container] = []
        self._monitors: dict[Container, Any] = {}
        self._old_data: dict[str, Any] = {}

    async def init(self) -> None:
        """Init the coordinator."""
        await self._refresh_docker_client()
        await self._init()
        await self._start_listening_events()

    async def restart_container(self, name: str) -> None:
        """Restart container if found."""
        container: Container = await self._get_container(name)
        if container:
            await self.hass.async_add_executor_job(container.restart)

    async def start_container(self, name: str) -> None:
        """Start container if found."""
        container: Container = await self._get_container(name)
        if container:
            await self.hass.async_add_executor_job(container.start)

    async def stop_container(self, name: str) -> None:
        """Stop container if found."""
        container: Container = await self._get_container(name)
        if container:
            await self.hass.async_add_executor_job(container.stop)

    async def _refresh_docker_client(self) -> None:
        def get_client():
            return DockerClient(base_url=self._url)

        self._docker = await self.hass.async_add_executor_job(get_client)

    async def _get_container_list(self) -> list[Container]:
        return await self.hass.async_add_executor_job(
            self._docker.containers.list, *{"all": True}
        )

    async def _get_container(self, name: str) -> Container | None:
        return next(
            container for container in self._containers if container.name == name
        )

    async def _init(self):
        self._containers = await self._get_container_list()
        self._monitors = {
            container: await self.hass.async_add_executor_job(
                partial(container.stats, **{"decode": True, "stream": True})
            )
            for container in self._containers
        }

    async def _start_listening_events(self):
        def events():
            self.logger.debug("Starting listening to events")
            filters = {"event": ["start", "stop", "create", "destroy"]}
            for evt in self._docker.events(decode=True, filters=filters):
                self.logger.debug("Received event %s", evt)
                self.hass.add_job(self._init)

            self.logger.debug("Event listening stopped")

        thread = threading.Thread(target=events)
        thread.start()
        self.logger.debug("Events listener thread started")

    async def _refresh(self):
        containers_data = {container.name: {} for container in self._containers}
        try:
            need_refresh = False

            for container, stats in self._monitors.items():
                containers_data[container.name]["id"] = container.attrs["Id"]
                containers_data[container.name]["status"] = container.status

                if container.status == "running":
                    containers_data[container.name][
                        "started_at"
                    ] = DockerMonitorCoordinator._to_date(
                        container.attrs["State"]["StartedAt"]
                    )

                    stat = DockerMonitorCoordinator._skip_old_stat(stats)
                    need_refresh = stat is None or need_refresh

                    if stat:
                        cpu_new = DockerMonitorCoordinator._cpu_compute(
                            self._old_data.get(container.name, {}).get("cpu", {}), stat
                        )
                        mem_new = DockerMonitorCoordinator._mem_compute(stat)
                        net_new = DockerMonitorCoordinator._network_compute(
                            self._old_data.get(container.name, {}).get("net", {}), stat
                        )
                        containers_data[container.name]["cpu"] = cpu_new
                        containers_data[container.name]["mem"] = mem_new
                        containers_data[container.name]["net"] = net_new

            _LOGGER.debug("new data are %s", containers_data)
            self._old_data = containers_data

            if need_refresh:
                self.logger.debug("Some refresh needed")
                await self._init()
        except Exception:  # pylint: disable=broad-except
            await self._refresh_docker_client()
            await self._init()
            raise
        return containers_data

    @staticmethod
    def _skip_old_stat(stats):
        for stat in stats:
            now = datetime.now(tz=timezone.utc).replace(microsecond=0)
            update = DockerMonitorCoordinator._to_date(stat["read"]).replace(
                microsecond=0
            )
            if now == update:
                return stat

    @staticmethod
    def _cpu_compute(cpu_old, stat):
        cpu_new = {
            "container": stat["cpu_stats"]["cpu_usage"]["total_usage"],
            "system": stat["cpu_stats"]["system_cpu_usage"],
        }

        cpu_pct = 0
        if cpu_old:
            cpu_delta = float(cpu_new["container"] - cpu_old["container"])
            system_delta = float(cpu_new["system"] - cpu_old["system"])

            if cpu_delta > 0 and system_delta > 0:
                cpu_pct = (
                    (cpu_delta / system_delta)
                    * float(stat["cpu_stats"]["online_cpus"])
                    * 100.0
                )

        cpu_new["percentage"] = cpu_pct
        return cpu_new

    @staticmethod
    def _mem_compute(stat):
        mem = {
            "usage": float(stat["memory_stats"]["usage"])
            - float(stat["memory_stats"]["stats"]["inactive_file"]),
            "max": float(stat["memory_stats"]["limit"]),
        }

        mem["percentage"] = (mem["usage"] / mem["max"]) * 100
        return mem

    @staticmethod
    def _network_compute(net_old, stat):
        net_new = {
            "interfaces": {},
            "total": {"tx_bytes": 0, "rx_bytes": 0, "speed_tx": 0, "speed_rx": 0},
            "last_update": DockerMonitorCoordinator._to_date(stat["read"]),
        }

        for if_name, network_stat in stat["networks"].items():
            net_new["interfaces"][if_name] = {}
            net_new["interfaces"][if_name]["tx_bytes"] = network_stat["tx_bytes"]
            net_new["interfaces"][if_name]["rx_bytes"] = network_stat["rx_bytes"]
            net_new["total"]["tx_bytes"] += network_stat["tx_bytes"]
            net_new["total"]["rx_bytes"] += network_stat["rx_bytes"]

        if net_old:
            delta_tx = net_new["total"]["tx_bytes"] - net_old["total"]["tx_bytes"]
            delta_rx = net_new["total"]["rx_bytes"] - net_old["total"]["rx_bytes"]
            time = (net_new["last_update"] - net_old["last_update"]).total_seconds()
            net_new["total"]["speed_tx"] = delta_tx / time
            net_new["total"]["speed_rx"] = delta_rx / time

            for if_name, intf in net_new["interfaces"].items():
                delta_tx = intf["tx_bytes"] - net_old["interfaces"][if_name]["tx_bytes"]
                delta_rx = intf["rx_bytes"] - net_old["interfaces"][if_name]["rx_bytes"]

                intf["speed_tx"] = delta_tx / time
                intf["speed_rx"] = delta_rx / time

        return net_new

    @staticmethod
    def _to_date(date_str: str) -> datetime:
        to_parse = date_str[:-4] + date_str[-1:]
        return datetime.strptime(to_parse, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )
