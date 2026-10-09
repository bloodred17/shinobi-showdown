//! Versioned gameplay content schemas and startup validation.

use serde::{Deserialize, Serialize};
use shinobi_game_domain::TileCoordinate;
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MapDefinition {
    pub schema_version: u16,
    pub id: String,
    pub width: u16,
    pub height: u16,
    pub spawn_tiles: Vec<TileCoordinate>,
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ContentValidationError {
    #[error("map dimensions must be non-zero")]
    EmptyMap,
    #[error("the M0 fixture requires exactly six unique spawn tiles")]
    InvalidSpawnCount,
    #[error("spawn tile ({x}, {y}) is outside the map")]
    SpawnOutOfBounds { x: u16, y: u16 },
}

impl MapDefinition {
    pub fn validate(&self) -> Result<(), ContentValidationError> {
        if self.width == 0 || self.height == 0 {
            return Err(ContentValidationError::EmptyMap);
        }

        let mut unique_spawns = self.spawn_tiles.clone();
        unique_spawns.sort_unstable_by_key(|tile| (tile.x, tile.y));
        unique_spawns.dedup();
        if unique_spawns.len() != 6 {
            return Err(ContentValidationError::InvalidSpawnCount);
        }

        if let Some(tile) = unique_spawns
            .iter()
            .find(|tile| !tile.is_within(self.width, self.height))
        {
            return Err(ContentValidationError::SpawnOutOfBounds {
                x: tile.x,
                y: tile.y,
            });
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::MapDefinition;

    #[test]
    fn validates_the_checked_in_m0_map() {
        let definition: MapDefinition = serde_json::from_str(include_str!(
            "../../../content/maps/m0-isometric-spike.json"
        ))
        .expect("fixture must deserialize");

        assert_eq!(definition.schema_version, 1);
        assert_eq!(definition.width, 8);
        definition.validate().expect("fixture must be valid");
    }
}
