from io import BytesIO
import fnmatch
import zipfile


def extract(zip_content, include_patterns=None, exclude_patterns=None):
    """
    This generator return pairs of (filename, BytesIO) extracted from zip archive which is also
    a BytesIO object.

    Args:
        zip_path (str): Path to zip archive.
        include_pattern (str): Pattern to include files.
        exclude_pattern (str): Pattern to exclude files.

    Returns:
        list: List of extracted files.

    """
    with zipfile.ZipFile(zip_content) as zip_file:
        for name in zip_file.namelist():
            if include_patterns and not any(fnmatch.fnmatch(name, p) for p in include_patterns):
                continue
            if exclude_patterns and any(fnmatch.fnmatch(name, p) for p in exclude_patterns):
                continue
            yield (name, BytesIO(zip_file.read(name)))
