"""
Configuration settings for the image resizer application.
"""

import os
from typing import Dict, Any

# Default resize settings
DEFAULT_CONFIG = {
    'resize': {
        'width': 800,
        'height': 600,
        'quality': 85,
        'format': 'JPEG',
        'mode': 'fit',
        'preserve_aspect': True,
        'preserve_metadata': False,
        'lossless': False,
        'max_workers': None,  # Auto-detect
        'naming_pattern': '{name}_resized'
    },
    'ui': {
        'max_file_size_mb': 50,
        'max_files_per_batch': 100,
        'supported_formats': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'gif'],
        'output_formats': ['JPEG', 'PNG', 'WEBP']
    },
    'paths': {
        'output_dir': 'resized_images',
        'temp_dir': None  # Use system default
    }
}

# Format compression settings
FORMAT_SETTINGS = {
    'JPEG': {
        'name': 'JPEG',
        'supports_lossless': False,
        'supports_transparency': False,
        'description': 'Lossy compression, best for photos'
    },
    'PNG': {
        'name': 'PNG',
        'supports_lossless': True,
        'supports_transparency': True,
        'description': 'Lossless compression, preserves transparency'
    },
    'WEBP': {
        'name': 'WebP',
        'supports_lossless': True,
        'supports_transparency': True,
        'description': 'Modern format with lossy or lossless compression'
    }
}

# Resize mode descriptions
RESIZE_MODES = {
    'fit': {
        'name': 'Fit',
        'description': 'Fit image within dimensions, preserving aspect ratio',
        'icon': '📐'
    },
    'fill': {
        'name': 'Fill',
        'description': 'Fill dimensions, may crop parts of the image',
        'icon': '🔲'
    },
    'crop': {
        'name': 'Crop',
        'description': 'Crop to exact dimensions, preserving aspect ratio',
        'icon': '✂️'
    },
    'stretch': {
        'name': 'Stretch',
        'description': 'Stretch to exact dimensions, may distort image',
        'icon': '↔️'
    }
}

# Naming pattern examples
NAMING_PATTERNS = {
    'Default': '{name}_resized',
    'With Size': '{name}_{width}x{height}',
    'Sequential': 'img_{index:03d}',
    'Original': '{original_name}',
    'Custom': '{name}_{width}x{height}_resized'
}

def get_config() -> Dict[str, Any]:
    """Get the current configuration."""
    return DEFAULT_CONFIG.copy()

def update_config(updates: Dict[str, Any]) -> None:
    """Update configuration with new values."""
    global DEFAULT_CONFIG
    for section, values in updates.items():
        if section in DEFAULT_CONFIG:
            DEFAULT_CONFIG[section].update(values)

def get_resize_mode_info(mode: str) -> Dict[str, str]:
    """Get information about a resize mode."""
    return RESIZE_MODES.get(mode, RESIZE_MODES['fit'])

def get_all_resize_modes() -> Dict[str, Dict[str, str]]:
    """Get all available resize modes."""
    return RESIZE_MODES.copy()

def get_format_settings(format: str) -> Dict[str, Any]:
    """Get settings for a specific output format."""
    return FORMAT_SETTINGS.get(format.upper(), FORMAT_SETTINGS['JPEG'])

def supports_lossless(format: str) -> bool:
    """Check if a format supports lossless compression."""
    return get_format_settings(format).get('supports_lossless', False)

def get_all_formats() -> Dict[str, Dict[str, Any]]:
    """Get all available output formats."""
    return FORMAT_SETTINGS.copy()