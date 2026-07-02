"""标签功能测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pygit.commit import commit_index
from pygit.objects import read_object
from pygit.refs import read_ref
from pygit.repository import init_repository
from pygit.tag import create_annotated_tag, create_lightweight_tag, list_tags
from pygit.working_tree import add_paths


class TagTests(unittest.TestCase):
    """验证轻量标签和附注标签。"""

    def test_create_lightweight_tag(self) -> None:
        """轻量标签应直接指向目标 commit。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])
            commit_oid = commit_index(repo, "initial\n")

            create_lightweight_tag(repo, "v1.0.0", commit_oid)

            self.assertEqual(read_ref(repo, "refs/tags/v1.0.0"), commit_oid)
            self.assertEqual(list_tags(repo), ["v1.0.0"])

    def test_create_annotated_tag(self) -> None:
        """附注标签应创建 tag 对象，并让 refs/tags 指向 tag 对象。"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = init_repository(root)
            (root / "hello.txt").write_bytes(b"hello\n")
            add_paths(repo, [Path("hello.txt")])
            commit_oid = commit_index(repo, "initial\n")

            tag_oid = create_annotated_tag(repo, "v1.0.0", commit_oid, "release\n")
            tag_obj = read_object(repo, tag_oid)

            self.assertEqual(tag_obj.object_type, "tag")
            self.assertIn(f"object {commit_oid}\n".encode("utf-8"), tag_obj.content)
            self.assertEqual(read_ref(repo, "refs/tags/v1.0.0"), tag_oid)


if __name__ == "__main__":
    unittest.main()

