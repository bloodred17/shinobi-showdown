//! Deterministic game rules and value objects.
//!
//! This crate deliberately has no graphics, filesystem, or network dependency.

use serde::{Deserialize, Serialize};

/// A logical tile coordinate. Pixel projection belongs to the rendering client.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TileCoordinate {
    pub x: u16,
    pub y: u16,
}

impl TileCoordinate {
    #[must_use]
    pub const fn new(x: u16, y: u16) -> Self {
        Self { x, y }
    }

    #[must_use]
    pub const fn manhattan_distance(self, other: Self) -> u16 {
        self.x.abs_diff(other.x) + self.y.abs_diff(other.y)
    }

    #[must_use]
    pub const fn is_within(self, width: u16, height: u16) -> bool {
        self.x < width && self.y < height
    }
}

#[cfg(test)]
mod tests {
    use super::TileCoordinate;

    #[test]
    fn logical_coordinates_are_bounded_independently_of_rendering() {
        let tile = TileCoordinate::new(7, 4);

        assert!(tile.is_within(8, 8));
        assert!(!tile.is_within(7, 8));
        assert_eq!(tile.manhattan_distance(TileCoordinate::new(2, 2)), 7);
    }
}
