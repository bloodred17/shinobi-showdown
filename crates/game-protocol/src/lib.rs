//! Player-safe network and interop data transfer objects.
//!
//! Authoritative match state must never be serialized through these types.

use serde::{Deserialize, Serialize};
use ts_rs::TS;

pub const PROTOCOL_VERSION: &str = "0.1.0";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(rename_all = "camelCase")]
pub struct TileCoordinateDto {
    pub x: u16,
    pub y: u16,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, TS)]
#[serde(tag = "type", rename_all = "snake_case")]
#[ts(tag = "type", rename_all = "snake_case")]
pub enum ClientMessage {
    Ping { request_id: String },
    TileSelected { coordinate: TileCoordinateDto },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, TS)]
#[serde(tag = "type", rename_all = "snake_case")]
#[ts(tag = "type", rename_all = "snake_case")]
pub enum ServerMessage {
    Connected { protocol_version: String },
    Pong { request_id: String },
    TileSelected { coordinate: TileCoordinateDto },
    InvalidMessage,
}

#[cfg(test)]
mod tests {
    use super::{ClientMessage, TileCoordinateDto};

    #[test]
    fn client_messages_are_explicitly_discriminated() {
        let encoded = serde_json::to_value(ClientMessage::TileSelected {
            coordinate: TileCoordinateDto { x: 3, y: 5 },
        })
        .expect("message must serialize");

        assert_eq!(encoded["type"], "tile_selected");
        assert_eq!(encoded["coordinate"]["x"], 3);
    }
}
