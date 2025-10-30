import os
import git
from urllib.parse import urlparse

def clone_repository(repo_url: str, data_dir: str):
    """
    Clone a Git repository from the given URL.
    
    Args:
        repo_url: Full Git repository URL (e.g., https://github.com/user/repo.git)
        data_dir: Directory where the repository will be cloned
        
    Returns:
        Path to the cloned repository
        
    Raises:
        ValueError: If the URL is invalid
        git.GitCommandError: If cloning fails
    """
    # Validate URL
    if not repo_url or not repo_url.strip():
        raise ValueError("Repository URL cannot be empty")
    
    repo_url = repo_url.strip()
    
    # Basic validation for common Git hosting patterns
    if not any(host in repo_url.lower() for host in ['github.com', 'gitlab.com', 'bitbucket.org', '.git']):
        raise ValueError("Invalid Git repository URL. Please provide a valid GitHub, GitLab, or Bitbucket URL")
    
    # Extract repository name from URL
    # Handle various URL formats:
    # - https://github.com/user/repo.git
    # - https://github.com/user/repo
    # - git@github.com:user/repo.git
    try:
        if repo_url.startswith('git@'):
            # SSH format: git@github.com:user/repo.git
            repo_name = repo_url.split(':')[-1].split('/')[-1].replace('.git', '')
        else:
            # HTTP(S) format
            parsed = urlparse(repo_url)
            path_parts = [p for p in parsed.path.split('/') if p]
            if not path_parts:
                raise ValueError("Could not extract repository name from URL")
            repo_name = path_parts[-1].replace('.git', '')
    except Exception as e:
        raise ValueError(f"Failed to parse repository URL: {str(e)}")
    
    if not repo_name:
        raise ValueError("Could not determine repository name from URL")
    
    repo_path = os.path.join(data_dir, repo_name)

    # If repo already exists, pull latest changes
    if os.path.exists(repo_path):
        try:
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull()
        except Exception as e:
            raise Exception(f"Failed to update existing repository: {str(e)}")
    else:
        try:
            git.Repo.clone_from(repo_url, repo_path)
        except git.GitCommandError as e:
            raise Exception(f"Failed to clone repository: {str(e)}")

    return repo_path

