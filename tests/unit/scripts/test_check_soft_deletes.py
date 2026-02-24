"""Tests for check_soft_deletes.py — detect hard deletes on soft-deleteable tables."""

from scripts.check_soft_deletes import (
    find_direct_delete_chains,
    has_supports_soft_delete,
)


class TestSoftDeleteDetection:
    """Detect supports_soft_delete = True in class definitions."""

    def test_detects_supports_soft_delete_attribute(self) -> None:
        source = (
            "class DocumentRepository(BaseRepository):\n"
            "    def __init__(self, client):\n"
            '        super().__init__("documents", client, supports_soft_delete=True)\n'
        )
        assert has_supports_soft_delete(source) is True

    def test_ignores_repos_without_soft_delete(self) -> None:
        source = (
            "class CommentRepository(BaseRepository):\n"
            "    def __init__(self, client):\n"
            '        super().__init__("comments", client)\n'
        )
        assert has_supports_soft_delete(source) is False

    def test_detects_soft_delete_false(self) -> None:
        source = (
            "class JobRepository(BaseRepository):\n"
            "    def __init__(self, client):\n"
            '        super().__init__("jobs", client, supports_soft_delete=False)\n'
        )
        assert has_supports_soft_delete(source) is False


class TestDirectDeleteChainDetection:
    """Detect .delete().eq() chains that bypass soft-delete."""

    def test_detects_direct_delete_chain(self) -> None:
        source = (
            "class DocumentRepository(BaseRepository):\n"
            "    async def hard_remove(self, id):\n"
            '        self.client.table(self.table_name).delete().eq("id", id).execute()\n'
        )
        violations = find_direct_delete_chains(source)
        assert len(violations) == 1

    def test_allows_base_repository_delete(self) -> None:
        """The base delete() method is allowed since it handles soft-delete internally."""
        source = (
            "class BaseRepository(ABC):\n"
            "    async def delete(self, id: str) -> bool:\n"
            "        if self.supports_soft_delete:\n"
            "            data = {'deleted_at': 'now'}\n"
            "            result = await self.update(id, data)\n"
            "            return result is not None\n"
            "        else:\n"
            '            self.client.table(self.table_name).delete().eq("id", id).execute()\n'
            "            return True\n"
        )
        violations = find_direct_delete_chains(source)
        assert len(violations) == 0

    def test_noqa_suppression(self) -> None:
        source = (
            "class DocumentRepository(BaseRepository):\n"
            "    async def purge(self, id):\n"
            '        self.client.table(self.table_name).delete().eq("id", id).execute()  # noqa: hard-delete\n'
        )
        violations = find_direct_delete_chains(source)
        assert len(violations) == 0

    def test_detects_multiline_delete_chain(self) -> None:
        source = (
            "class DocumentRepository(BaseRepository):\n"
            "    async def purge(self, id):\n"
            "        response = (\n"
            "            self.client.table(self.table_name)\n"
            "            .delete()\n"
            "            .eq('id', id)\n"
            "            .execute()\n"
            "        )\n"
        )
        violations = find_direct_delete_chains(source)
        assert len(violations) == 1

    def test_ignores_non_self_client_deletes(self) -> None:
        """Delete calls that aren't on self.client should be ignored."""
        source = (
            "class SomeService:\n"
            "    async def cleanup(self):\n"
            '        other_client.table("foo").delete().eq("id", id).execute()\n'
        )
        violations = find_direct_delete_chains(source)
        assert len(violations) == 0
