"""pygit 专用 TCP 服务器。

本服务器不是官方 Git wire protocol，也不面向 GitHub 或 git-upload-pack。
它是 `.pygit` 专用的自建服务端，使用标准库 socketserver 和 JSON-lines
协议提供 refs、fetch、push。协议只传输本项目的对象和引用，便于自建服务器
使用，同时避免把官方 Git 协议复杂度混入本项目边界。
"""

from __future__ import annotations

import base64
import json
import socket
import socketserver
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import PygitError
from .merge import ancestors_by_distance
from .objects import GitObject, encode_object, read_object, write_object
from .refs import list_branches, read_ref, update_ref
from .repository import Repository, find_repository


class ServerError(PygitError):
    """pygit 专用服务器协议或请求处理失败时抛出。"""


@dataclass(frozen=True)
class PygitRemoteURL:
    """解析后的 pygit 专用远端地址。"""

    host: str
    port: int


def parse_pygit_url(url: str) -> PygitRemoteURL | None:
    """解析 `pygit://host:port` 地址，非 pygit URL 返回 None。"""

    prefix = "pygit://"
    if not url.startswith(prefix):
        return None
    rest = url[len(prefix) :]
    host, sep, port_text = rest.partition(":")
    if not sep or not host or not port_text:
        raise ServerError(f"invalid pygit remote url: {url}")
    return PygitRemoteURL(host=host, port=int(port_text))


def serve(repo_path: Path, host: str = "127.0.0.1", port: int = 0) -> socketserver.ThreadingTCPServer:
    """启动 pygit 专用 TCP 服务并返回 server 对象。

    调用方可以在测试或 CLI 中决定是否调用 `serve_forever`。返回对象带有
    `server_address`，端口为 0 时可据此获取系统分配的实际端口。
    """

    repo = find_repository(repo_path)

    class Handler(PygitRequestHandler):
        repository = repo

    server = socketserver.ThreadingTCPServer((host, port), Handler)
    server.daemon_threads = True
    return server


class PygitRequestHandler(socketserver.StreamRequestHandler):
    """处理单个 JSON-lines 请求。"""

    repository: Repository

    def handle(self) -> None:
        """读取一行请求，写回一行响应。"""

        line = self.rfile.readline()
        if not line:
            return
        try:
            request = json.loads(line.decode("utf-8"))
            response = handle_request(self.repository, request)
        except Exception as exc:
            response = {"ok": False, "error": str(exc)}
        self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))


def handle_request(repo: Repository, request: dict[str, Any]) -> dict[str, Any]:
    """根据 action 分发专用远端请求。"""

    action = request.get("action")
    if action == "refs":
        return {"ok": True, "refs": refs_payload(repo)}
    if action == "fetch":
        return {"ok": True, "refs": refs_payload(repo), "objects": objects_payload(repo)}
    if action == "push":
        branch = request["branch"]
        new_oid = request["new"]
        old_oid = request.get("old")
        objects = request.get("objects", [])
        current = read_ref(repo, f"refs/heads/{branch}")
        if old_oid is not None and current != old_oid:
            return {"ok": False, "error": "non-fast-forward push rejected"}
        write_objects_payload(repo, objects)
        if current is not None and current not in ancestors_by_distance(repo, new_oid):
            return {"ok": False, "error": "non-fast-forward push rejected"}
        update_ref(repo, f"refs/heads/{branch}", new_oid)
        return {"ok": True, "new": new_oid}
    raise ServerError(f"unsupported action: {action}")


def refs_payload(repo: Repository) -> dict[str, str]:
    """返回本地分支引用表。"""

    refs: dict[str, str] = {}
    for branch in list_branches(repo):
        oid = read_ref(repo, f"refs/heads/{branch}")
        if oid is not None:
            refs[branch] = oid
    return refs


def objects_payload(repo: Repository) -> list[dict[str, str]]:
    """把本仓库可达 loose/pack 对象编码为传输负载。

    当前专用服务器按对象 ID 全量传输，保持协议简单可靠；对象内容传输的是
    Git 标准未压缩对象字节，客户端再按本地对象库格式写入。
    """

    seen: set[str] = set()
    payload: list[dict[str, str]] = []
    for oid in refs_payload(repo).values():
        for reachable in walk_reachable_objects(repo, oid):
            if reachable.oid in seen:
                continue
            seen.add(reachable.oid)
            raw = encode_object(reachable.object_type, reachable.content)
            payload.append({"oid": reachable.oid, "raw": base64.b64encode(raw).decode("ascii")})
    return payload


def write_objects_payload(repo: Repository, objects: list[dict[str, str]]) -> None:
    """写入客户端推送来的对象负载。"""

    for item in objects:
        raw = base64.b64decode(item["raw"])
        from .objects import decode_raw_object

        obj = decode_raw_object(raw, expected_oid=item["oid"])
        write_object(repo, obj.object_type, obj.content)


def walk_reachable_objects(repo: Repository, commit_oid: str) -> list[GitObject]:
    """从 commit 出发收集 commit/tree/blob/tag 对象。"""

    objects: list[GitObject] = []
    seen: set[str] = set()

    def visit(oid: str) -> None:
        if oid in seen:
            return
        seen.add(oid)
        obj = read_object(repo, oid)
        objects.append(obj)
        if obj.object_type == "commit":
            text = obj.content.decode("utf-8")
            for line in text.splitlines():
                if line.startswith("tree ") or line.startswith("parent "):
                    visit(line.split(" ", 1)[1])
        elif obj.object_type == "tree":
            cursor = 0
            while cursor < len(obj.content):
                nul = obj.content.find(b"\x00", cursor)
                child_oid = obj.content[nul + 1 : nul + 21].hex()
                visit(child_oid)
                cursor = nul + 21
        elif obj.object_type == "tag":
            for line in obj.content.decode("utf-8").splitlines():
                if line.startswith("object "):
                    visit(line.split(" ", 1)[1])

    visit(commit_oid)
    return objects


def request(url: PygitRemoteURL, payload: dict[str, Any]) -> dict[str, Any]:
    """向 pygit 专用服务器发送单个 JSON-lines 请求。"""

    with socket.create_connection((url.host, url.port), timeout=5) as sock:
        file = sock.makefile("rwb")
        file.write((json.dumps(payload) + "\n").encode("utf-8"))
        file.flush()
        response_line = file.readline()
    if not response_line:
        raise ServerError("empty response from pygit server")
    response = json.loads(response_line.decode("utf-8"))
    if not response.get("ok"):
        raise ServerError(response.get("error", "pygit server request failed"))
    return response

