#!/usr/bin/env python3
"""
Script to reorganize files according to the standardized directory structure.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory structure definition
DIRECTORY_STRUCTURE = {
    'core': {
        'config': ['*.py', '*.yaml', '*.json'],
        'database': ['*.py', 'migrations/*'],
        'services': ['*.py'],
        'utils': ['*.py'],
    },
    'api': {
        'v1': ['*.py'],
        'middleware': ['*.py'],
    },
    'web': {
        'components': ['*.tsx', '*.jsx', '*.css'],
        'pages': ['*.tsx', '*.jsx', '*.css'],
        'utils': ['*.ts', '*.js'],
    },
    'tests': {
        'unit': ['test_*.py'],
        'integration': ['test_*.py'],
        'e2e': ['test_*.py'],
    },
    'scripts': ['*.py', '*.sh'],
    'docs': {
        'api': ['*.md'],
        'maintenance': ['*.md'],
        'user': ['*.md'],
    },
    'tools': ['*.py', '*.sh'],
}

def create_directory_structure(base_path: Path) -> None:
    """Create the directory structure if it doesn't exist."""
    def create_dirs(structure: Dict, current_path: Path) -> None:
        for key, value in structure.items():
            path = current_path / key
            path.mkdir(parents=True, exist_ok=True)
            if isinstance(value, dict):
                create_dirs(value, path)

    create_dirs(DIRECTORY_STRUCTURE, base_path)
    logger.info("Directory structure created successfully")

def get_file_mapping(base_path: Path) -> Dict[str, str]:
    """Generate mapping of files to their new locations."""
    file_mapping = {}
    
    def should_move_file(file_path: Path, patterns: List[str]) -> bool:
        """Check if file matches any of the patterns."""
        return any(file_path.match(pattern) for pattern in patterns)

    def map_files(structure: Dict, current_path: Path) -> None:
        for item in current_path.rglob('*'):
            if not item.is_file():
                continue

            rel_path = item.relative_to(base_path)
            for dir_path, patterns in get_flat_structure(structure).items():
                if should_move_file(rel_path, patterns):
                    new_path = base_path / dir_path / item.name
                    if new_path != item:
                        file_mapping[str(item)] = str(new_path)
                    break

    def get_flat_structure(structure: Dict, prefix: str = '') -> Dict[str, List[str]]:
        """Convert nested structure to flat dictionary with full paths."""
        result = {}
        for key, value in structure.items():
            current_prefix = f"{prefix}/{key}" if prefix else key
            if isinstance(value, dict):
                result.update(get_flat_structure(value, current_prefix))
            else:
                result[current_prefix] = value
        return result

    map_files(DIRECTORY_STRUCTURE, base_path)
    return file_mapping

def move_files(file_mapping: Dict[str, str]) -> None:
    """Move files to their new locations."""
    moved_files: Set[str] = set()
    
    for src, dst in file_mapping.items():
        try:
            if src == dst or src in moved_files:
                continue

            dst_dir = os.path.dirname(dst)
            os.makedirs(dst_dir, exist_ok=True)

            if os.path.exists(dst):
                logger.warning(f"Destination file already exists: {dst}")
                continue

            shutil.move(src, dst)
            moved_files.add(src)
            logger.info(f"Moved {src} -> {dst}")

        except Exception as e:
            logger.error(f"Error moving {src} to {dst}: {e}")

def main() -> None:
    """Main function to reorganize files."""
    try:
        base_path = Path.cwd()
        
        # Create directory structure
        create_directory_structure(base_path)

        # Generate file mapping
        file_mapping = get_file_mapping(base_path)

        # Preview changes
        logger.info("\nProposed file moves:")
        for src, dst in file_mapping.items():
            logger.info(f"{src} -> {dst}")

        # Confirm with user
        response = input("\nProceed with file moves? (y/n): ")
        if response.lower() != 'y':
            logger.info("Operation cancelled")
            return

        # Move files
        move_files(file_mapping)
        logger.info("File reorganization completed successfully")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main() 