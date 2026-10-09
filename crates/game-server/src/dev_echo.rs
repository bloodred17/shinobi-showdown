use axum::{
    extract::{WebSocketUpgrade, ws::Message},
    http::{HeaderMap, StatusCode, header::ORIGIN},
    response::{IntoResponse, Response},
};
use futures_util::{SinkExt, StreamExt};
use shinobi_game_protocol::{ClientMessage, PROTOCOL_VERSION, ServerMessage};

const ALLOWED_DEV_ORIGINS: [&str; 2] = ["http://localhost:4200", "http://127.0.0.1:4200"];

pub(crate) async fn upgrade(headers: HeaderMap, websocket: WebSocketUpgrade) -> Response {
    let Some(origin) = headers.get(ORIGIN).and_then(|value| value.to_str().ok()) else {
        return StatusCode::FORBIDDEN.into_response();
    };

    if !is_allowed_origin(origin) {
        return StatusCode::FORBIDDEN.into_response();
    }

    websocket.on_upgrade(handle_socket)
}

fn is_allowed_origin(origin: &str) -> bool {
    ALLOWED_DEV_ORIGINS.contains(&origin)
}

async fn handle_socket(socket: axum::extract::ws::WebSocket) {
    let (mut sender, mut receiver) = socket.split();
    let connected = ServerMessage::Connected {
        protocol_version: PROTOCOL_VERSION.to_owned(),
    };

    if send_json(&mut sender, &connected).await.is_err() {
        return;
    }

    while let Some(Ok(message)) = receiver.next().await {
        let Message::Text(text) = message else {
            if matches!(message, Message::Close(_)) {
                return;
            }
            continue;
        };

        let response = match serde_json::from_str::<ClientMessage>(&text) {
            Ok(ClientMessage::Ping { request_id }) => ServerMessage::Pong { request_id },
            Ok(ClientMessage::TileSelected { coordinate }) => {
                ServerMessage::TileSelected { coordinate }
            }
            Err(_) => ServerMessage::InvalidMessage,
        };

        if send_json(&mut sender, &response).await.is_err() {
            return;
        }
    }
}

async fn send_json(
    sender: &mut futures_util::stream::SplitSink<axum::extract::ws::WebSocket, Message>,
    message: &ServerMessage,
) -> Result<(), axum::Error> {
    let encoded = serde_json::to_string(message).expect("server messages must serialize");
    sender.send(Message::Text(encoded.into())).await
}

#[cfg(test)]
mod tests {
    use super::is_allowed_origin;

    #[test]
    fn development_echo_accepts_only_the_known_angular_origins() {
        assert!(is_allowed_origin("http://localhost:4200"));
        assert!(is_allowed_origin("http://127.0.0.1:4200"));
        assert!(!is_allowed_origin("https://example.invalid"));
    }
}
