from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "k8s-platform-api"
    app_version: str = "0.1.0"
    inventory: str = "inventories/hosts-container.yml"
    project_root: str = ".."
    ansible_playbook_bin: str = "ansible-playbook"
    task_log_dir: str = "/tmp/k8s-platform-api/tasks"
    dry_run_default: bool = True


settings = Settings()
