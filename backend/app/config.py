from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 7749
    cors_origins: str = "http://localhost:7751,http://127.0.0.1:7751"

    # Storage
    chroma_persist_dir: str = "./chroma_data"
    generated_agents_dir: str = "./generated_agents"
    session_max_age_hours: int = 24

    # Pipeline constants
    max_spec_iterations: int = 3
    max_build_iterations: int = 10
    max_builder_repair_iterations: int = 2
    max_elicitor_rounds: int = 3
    completeness_threshold: float = 0.7
    docker_timeout: int = 60
    pipeline_timeout: int = 300

    # Tester runtime
    tester_live_execution: bool = True
    tester_test_model: str = "openai/gpt-4o-mini"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Convenience aliases for backward compatibility
OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_BASE_URL = settings.openrouter_base_url
MAX_SPEC_ITERATIONS = settings.max_spec_iterations
MAX_BUILD_ITERATIONS = settings.max_build_iterations
MAX_ELICITOR_ROUNDS = settings.max_elicitor_rounds
COMPLETENESS_THRESHOLD = settings.completeness_threshold
DOCKER_TIMEOUT = settings.docker_timeout

# Model-per-agent routing — different models for different strengths
# Architect + Critic deliberately use different families for cross-model adversarial review
MODEL_ROUTING: dict[str, str] = {
    "elicitor": "openai/gpt-4o-mini",
    "architect": "anthropic/claude-sonnet-4-5",
    "critic": "openai/gpt-4o",
    "builder": "openai/gpt-4o",
    "tester": "openai/gpt-4o-mini",
    "learner": "openai/gpt-4o-mini",
}
