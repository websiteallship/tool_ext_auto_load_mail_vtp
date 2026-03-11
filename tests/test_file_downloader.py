"""Unit tests for FileDownloader."""

import pytest

from src.file_downloader import FileDownloader
from src.models import DownloadStatus


class TestSaveAttachment:
    def test_saves_file(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        result = dl.save_attachment(b"test data content", "test.pdf")

        assert result.status == DownloadStatus.SUCCESS
        assert result.filepath is not None
        assert result.filepath.exists()
        assert result.filepath.read_bytes() == b"test data content"
        assert result.size_bytes == len(b"test data content")

    def test_saves_to_subfolder(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        result = dl.save_attachment(b"data", "invoice.pdf", subfolder="viettel")

        assert result.status == DownloadStatus.SUCCESS
        assert (tmp_path / "viettel" / "invoice.pdf").exists()

    def test_empty_data_fails(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        result = dl.save_attachment(b"", "empty.pdf")

        assert result.status == DownloadStatus.FAILED

    def test_skip_duplicate(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path, skip_duplicates=True)

        # First save
        dl.save_attachment(b"data", "file.pdf")

        # Second save — should skip
        result = dl.save_attachment(b"data", "file.pdf")
        assert result.status == DownloadStatus.SKIPPED_DUPLICATE

    def test_no_skip_when_disabled(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path, skip_duplicates=False)

        dl.save_attachment(b"data1", "file.pdf")
        result = dl.save_attachment(b"data2", "file.pdf")

        assert result.status == DownloadStatus.SUCCESS


class TestIsDuplicate:
    def test_not_duplicate(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        assert dl.is_duplicate("nonexistent.pdf") is False

    def test_is_duplicate(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        (tmp_path / "exists.pdf").write_bytes(b"content")
        assert dl.is_duplicate("exists.pdf") is True

    def test_subfolder_duplicate(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "file.pdf").write_bytes(b"data")

        assert dl.is_duplicate("file.pdf", subfolder="sub") is True
        assert dl.is_duplicate("file.pdf", subfolder="other") is False


class TestSanitizeFilename:
    def test_removes_unsafe_chars(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        result = dl.save_attachment(b"data", 'file<>:"/\\|?*.pdf')
        assert result.status == DownloadStatus.SUCCESS
        assert "<" not in result.filepath.name

    def test_empty_filename(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        result = dl.save_attachment(b"data", "")
        assert result.status == DownloadStatus.SUCCESS


class TestGetDownloadCount:
    def test_empty_dir(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        assert dl.get_download_count() == 0

    def test_with_files(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        (tmp_path / "a.pdf").write_bytes(b"a")
        (tmp_path / "b.xml").write_bytes(b"b")
        assert dl.get_download_count() == 2

    def test_nonexistent_subfolder(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        assert dl.get_download_count(subfolder="nonexistent") == 0
