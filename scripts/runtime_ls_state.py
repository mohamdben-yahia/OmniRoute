from __future__ import annotations


class RuntimeLSBinding:
    def __init__(
        self,
        *,
        session_id: str,
        window_id: str,
        host: str,
        port: int,
        lifecycle_nonce: str,
        timestamp: float,
        csrf_token: str | None,
        state: str = "pending",
    ) -> None:
        self.session_id = session_id
        self.window_id = window_id
        self.host = host
        self.port = port
        self.lifecycle_nonce = lifecycle_nonce
        self.timestamp = timestamp
        self.csrf_token = csrf_token
        self.state = state

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class RuntimeLSRegistry:
    def __init__(self) -> None:
        self._current: RuntimeLSBinding | None = None

    def get_current(self) -> RuntimeLSBinding | None:
        if self._current is None:
            return None
        if self._current.state == "expired":
            return None
        return self._current

    def on_language_server_started(
        self,
        *,
        session_id: str,
        window_id: str,
        host: str,
        port: int,
        lifecycle_nonce: str,
        timestamp: float,
        csrf_token: str | None,
    ) -> RuntimeLSBinding:
        if self._current is not None and self._current.state != "expired":
            self._current.state = "expired"
        self._current = RuntimeLSBinding(
            session_id=session_id,
            window_id=window_id,
            host=host,
            port=port,
            lifecycle_nonce=lifecycle_nonce,
            timestamp=timestamp,
            csrf_token=csrf_token,
            state="pending",
        )
        return self._current

    def confirm(self, lifecycle_nonce: str) -> RuntimeLSBinding:
        if self._current is None or self._current.lifecycle_nonce != lifecycle_nonce:
            raise ValueError(f"No runtime LS binding for nonce {lifecycle_nonce}")
        self._current.state = "confirmed"
        return self._current

    def on_language_server_stopped(
        self,
        *,
        session_id: str,
        window_id: str,
        lifecycle_nonce: str,
        timestamp: float,
    ) -> RuntimeLSBinding:
        if self._current is None or self._current.lifecycle_nonce != lifecycle_nonce:
            raise ValueError(f"No runtime LS binding for nonce {lifecycle_nonce}")
        self._current.state = "expired"
        self._current.timestamp = timestamp
        return self._current
