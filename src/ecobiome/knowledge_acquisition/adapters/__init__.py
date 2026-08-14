"""Built-in EcoBiome Collector acquisition adapters."""

from ecobiome.knowledge_acquisition.adapters.local_file import LocalFileAdapter
from ecobiome.knowledge_acquisition.adapters.youtube import YouTubeAdapter

__all__ = ["LocalFileAdapter", "YouTubeAdapter"]
