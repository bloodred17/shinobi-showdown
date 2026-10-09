use axum::{Json, Router, routing::get};
use serde::Serialize;
use shinobi_game_protocol::PROTOCOL_VERSION;

#[cfg(feature = "dev-echo")]
mod dev_echo;

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: &'static str,
    protocol_version: &'static str,
}

pub fn app() -> Router {
    let router = Router::new().route("/health", get(health));

    #[cfg(feature = "dev-echo")]
    let router = router.route("/ws/dev/echo", get(dev_echo::upgrade));

    router
}

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok",
        protocol_version: PROTOCOL_VERSION,
    })
}
