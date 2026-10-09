use std::f32::consts::FRAC_PI_4;

use bevy::{prelude::*, window::WindowResolution};
use shinobi_game_domain::TileCoordinate;
use shinobi_game_protocol::TileCoordinateDto;

const MAP_WIDTH: u16 = 8;
const MAP_HEIGHT: u16 = 8;
const TILE_WIDTH: f32 = 64.0;
const TILE_HEIGHT: f32 = 32.0;

#[derive(Component)]
struct GridTile(TileCoordinate);

#[derive(Resource, Default)]
struct SelectedTile(Option<TileCoordinate>);

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn start_game() {
    App::new()
        .insert_resource(ClearColor(Color::srgb(0.025, 0.04, 0.07)))
        .init_resource::<SelectedTile>()
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "Shinobi Tactics — M0".to_owned(),
                canvas: Some("#shinobi-game".to_owned()),
                fit_canvas_to_parent: true,
                prevent_default_event_handling: false,
                resolution: WindowResolution::new(960, 540),
                ..default()
            }),
            ..default()
        }))
        .add_systems(Startup, setup_grid)
        .add_systems(Update, (pick_tile, highlight_selected).chain())
        .run();
}

fn setup_grid(mut commands: Commands) {
    commands.spawn(Camera2d);

    for y in 0..MAP_HEIGHT {
        for x in 0..MAP_WIDTH {
            let coordinate = TileCoordinate::new(x, y);
            let world = logical_to_world(coordinate);
            let shade = if (x + y) % 2 == 0 { 0.2 } else { 0.15 };

            commands.spawn((
                GridTile(coordinate),
                Sprite::from_color(Color::srgb(0.08, shade, 0.24), Vec2::splat(42.0)),
                Transform::from_xyz(world.x, world.y, -(x as f32 + y as f32) * 0.001)
                    .with_rotation(Quat::from_rotation_z(FRAC_PI_4))
                    .with_scale(Vec3::new(1.0, 0.5, 1.0)),
            ));
        }
    }
}

fn pick_tile(
    mouse: Res<ButtonInput<MouseButton>>,
    windows: Query<&Window>,
    cameras: Query<(&Camera, &GlobalTransform)>,
    mut selected: ResMut<SelectedTile>,
) {
    if !mouse.just_pressed(MouseButton::Left) {
        return;
    }

    let Ok(window) = windows.single() else {
        return;
    };
    let Some(cursor_position) = window.cursor_position() else {
        return;
    };
    let Ok((camera, camera_transform)) = cameras.single() else {
        return;
    };
    let Ok(world_position) = camera.viewport_to_world_2d(camera_transform, cursor_position) else {
        return;
    };
    let Some(coordinate) = world_to_logical(world_position) else {
        return;
    };

    selected.0 = Some(coordinate);
    dispatch_selected_tile(TileCoordinateDto {
        x: coordinate.x,
        y: coordinate.y,
    });
}

fn highlight_selected(selected: Res<SelectedTile>, mut tiles: Query<(&GridTile, &mut Sprite)>) {
    if !selected.is_changed() {
        return;
    }

    for (tile, mut sprite) in &mut tiles {
        sprite.color = if Some(tile.0) == selected.0 {
            Color::srgb(0.95, 0.56, 0.16)
        } else {
            let shade = if (tile.0.x + tile.0.y) % 2 == 0 {
                0.2
            } else {
                0.15
            };
            Color::srgb(0.08, shade, 0.24)
        };
    }
}

#[must_use]
fn logical_to_world(coordinate: TileCoordinate) -> Vec2 {
    let centered_x = coordinate.x as f32 - (MAP_WIDTH - 1) as f32 / 2.0;
    let centered_y = coordinate.y as f32 - (MAP_HEIGHT - 1) as f32 / 2.0;

    Vec2::new(
        (centered_x - centered_y) * TILE_WIDTH / 2.0,
        (centered_x + centered_y) * TILE_HEIGHT / 2.0,
    )
}

#[must_use]
fn world_to_logical(world: Vec2) -> Option<TileCoordinate> {
    let projected_x = world.x / (TILE_WIDTH / 2.0);
    let projected_y = world.y / (TILE_HEIGHT / 2.0);
    let centered_x = (projected_x + projected_y) / 2.0;
    let centered_y = (projected_y - projected_x) / 2.0;
    let x = (centered_x + (MAP_WIDTH - 1) as f32 / 2.0).round();
    let y = (centered_y + (MAP_HEIGHT - 1) as f32 / 2.0).round();

    if x < 0.0 || y < 0.0 {
        return None;
    }

    let coordinate = TileCoordinate::new(x as u16, y as u16);
    coordinate
        .is_within(MAP_WIDTH, MAP_HEIGHT)
        .then_some(coordinate)
}

#[cfg(target_arch = "wasm32")]
fn dispatch_selected_tile(coordinate: TileCoordinateDto) {
    use web_sys::{CustomEvent, CustomEventInit};

    let Ok(detail) = serde_wasm_bindgen::to_value(&coordinate) else {
        return;
    };
    let event_init = CustomEventInit::new();
    event_init.set_detail(&detail);
    let Ok(event) = CustomEvent::new_with_event_init_dict("shinobi:tile-selected", &event_init)
    else {
        return;
    };

    if let Some(window) = web_sys::window() {
        let _ = window.dispatch_event(&event);
    }
}

#[cfg(not(target_arch = "wasm32"))]
fn dispatch_selected_tile(_coordinate: TileCoordinateDto) {}

#[cfg(test)]
mod tests {
    use bevy::math::Vec2;
    use shinobi_game_domain::TileCoordinate;

    use super::{logical_to_world, world_to_logical};

    #[test]
    fn isometric_projection_round_trips_logical_tiles() {
        for coordinate in [
            TileCoordinate::new(0, 0),
            TileCoordinate::new(3, 5),
            TileCoordinate::new(7, 7),
        ] {
            assert_eq!(
                world_to_logical(logical_to_world(coordinate)),
                Some(coordinate)
            );
        }

        assert_eq!(world_to_logical(Vec2::new(10_000.0, 10_000.0)), None);
    }
}
