/**
 * Type definitions for the multi-room floor plan system.
 *
 * This file contains all TypeScript interfaces and types used
 * throughout the floor plan and room management components.
 */

// Basic geometric types
export interface Position {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface Bounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

// Room system types
export interface Room {
  id: string;
  name: string;
  type: RoomType;
  bounds: Bounds;
  properties: RoomProperties;
  accessibility?: RoomAccessibility;
}

export type RoomType =
  | 'bedroom'
  | 'kitchen'
  | 'living_room'
  | 'bathroom'
  | 'office'
  | 'studio'
  | 'dining_room'
  | 'hallway'
  | 'closet';

export interface RoomProperties {
  floor_color: string;
  floor_material: FloorMaterial;
  lighting_level: number; // 0.0 to 1.0
  temperature?: number;
}

export type FloorMaterial =
  | 'hardwood'
  | 'carpet'
  | 'tile'
  | 'laminate'
  | 'concrete'
  | 'marble';

export interface RoomAccessibility {
  is_accessible: boolean;
  entry_points: string[]; // Array of doorway IDs
}

// Wall system types
export interface Wall {
  id: string;
  name?: string;
  geometry: WallGeometry;
  properties: WallProperties;
  structural?: WallStructural;
}

export interface WallGeometry {
  start: Position;
  end: Position;
}

export interface WallProperties {
  type: WallType;
  thickness: number;
  material: WallMaterial;
  color: string;
}

export type WallType = 'interior' | 'exterior';

export type WallMaterial =
  | 'drywall'
  | 'brick'
  | 'concrete'
  | 'wood'
  | 'glass';

export interface WallStructural {
  is_load_bearing: boolean;
  can_have_doorways: boolean;
}

// Doorway system types
export interface Doorway {
  id: string;
  name?: string;
  wall_id: string;
  position: DoorwayPosition;
  connections: DoorwayConnections;
  properties: DoorwayProperties;
  accessibility?: DoorwayAccessibility;
  world_position?: Position; // Calculated world coordinates
}

export interface DoorwayPosition {
  position_on_wall: number; // 0.0 to 1.0
  width: number;
}

export interface DoorwayConnections {
  room_a: string;
  room_b: string;
}

export interface DoorwayProperties {
  type: DoorwayType;
  has_door: boolean;
  door_state?: DoorState;
}

export type DoorwayType = 'open' | 'door' | 'archway' | 'window';

export type DoorState = 'open' | 'closed' | 'locked';

export interface DoorwayAccessibility {
  is_accessible: boolean;
  requires_interaction: boolean;
}

// Furniture system types
export interface FurnitureItem {
  id: string;
  name: string;
  description?: string;
  type: FurnitureType;
  room_id?: string;
  position: FurniturePosition;
  geometry: FurnitureGeometry;
  properties: FurnitureProperties;
  visual: FurnitureVisual;
  functional?: FurnitureFunctional;
  states?: Record<string, any>;
}

export type FurnitureType =
  | 'furniture'
  | 'decoration'
  | 'appliance'
  | 'lighting'
  | 'electronics';

export interface FurniturePosition extends Position {
  rotation?: number; // 0-360 degrees
}

export interface FurnitureGeometry extends Size {
  shape?: FurnitureShape;
  shape_data?: any; // Additional shape data for complex shapes
}

export type FurnitureShape =
  | 'rectangle'
  | 'circle'
  | 'polygon'
  | 'L-shape'
  | 'custom';

export interface FurnitureProperties {
  solid: boolean;
  interactive: boolean;
  movable: boolean;
  z_index?: number;
}

export interface FurnitureVisual {
  color: string;
  material: FurnitureMaterial;
  style: FurnitureStyle;
  sprite?: string;
}

export type FurnitureMaterial =
  | 'wood'
  | 'metal'
  | 'fabric'
  | 'plastic'
  | 'glass'
  | 'leather'
  | 'ceramic';

export type FurnitureStyle =
  | 'modern'
  | 'traditional'
  | 'industrial'
  | 'minimalist'
  | 'vintage'
  | 'contemporary';

export interface FurnitureFunctional {
  can_sit_on: boolean;
  can_place_items_on: boolean;
  storage_capacity: number;
  requires_power?: boolean;
}

// Assistant system types
export interface Assistant {
  id: string;
  location: AssistantLocation;
  movement?: AssistantMovement;
  status: AssistantStatus;
  interaction?: AssistantInteraction;
}

export interface AssistantLocation {
  floor_plan_id?: string;
  room_id?: string;
  position: Position;
  facing: FacingDirection;
  facing_angle: number; // 0-360 degrees
}

export type FacingDirection = 'up' | 'down' | 'left' | 'right';

export interface AssistantMovement {
  is_moving: boolean;
  target?: AssistantTarget;
  path?: Position[];
  speed: number; // pixels per second
}

export interface AssistantTarget {
  position: Position;
  room_id?: string;
}

export interface AssistantStatus {
  action: AssistantAction;
  mood: AssistantMood;
  expression?: string;
  energy_level: number; // 0.0 to 1.0
  mode: AssistantMode;
}

export type AssistantAction =
  | 'idle'
  | 'walking'
  | 'sitting'
  | 'talking'
  | 'interacting'
  | 'thinking';

export type AssistantMood =
  | 'happy'
  | 'sad'
  | 'neutral'
  | 'excited'
  | 'tired'
  | 'confused'
  | 'focused';

export type AssistantMode =
  | 'active'
  | 'idle'
  | 'sleeping'
  | 'busy';

export interface AssistantInteraction {
  holding_object_id?: string;
  sitting_on_object_id?: string;
  interacting_with_object_id?: string;
}

// Floor plan system types
export interface FloorPlan {
  id: string;
  name: string;
  description?: string;
  category: FloorPlanCategory;
  dimensions: FloorPlanDimensions;
  styling: FloorPlanStyling;
  rooms: Room[];
  walls: Wall[];
  doorways: Doorway[];
  furniture: FurnitureItem[];
  metadata?: FloorPlanMetadata;
}

export type FloorPlanCategory =
  | 'apartment'
  | 'house'
  | 'office'
  | 'studio'
  | 'commercial'
  | 'custom';

export interface FloorPlanDimensions extends Size {
  scale: number; // pixels per unit
  units: MeasurementUnit;
}

export type MeasurementUnit = 'feet' | 'meters' | 'pixels';

export interface FloorPlanStyling {
  background_color: string;
  background_image?: string;
  wall_color: string;
  wall_thickness: number;
}

export interface FloorPlanMetadata {
  created_at?: string;
  created_by?: string;
  is_template: boolean;
  is_active?: boolean;
  version?: string;
}

// Viewport and rendering types
export interface ViewBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ViewportState {
  viewBox: ViewBox;
  scale: number;
  center: Position;
  bounds: Bounds;
}

// Event handler types
export type ObjectClickHandler = (objectId: string) => void;
export type PositionClickHandler = (position: Position) => void;
export type AssistantMoveHandler = (position: Position) => void;
export type RoomChangeHandler = (roomId: string) => void;

// API response types
export interface FloorPlanResponse {
  floor_plan: FloorPlan;
  assistant: Assistant;
  success: boolean;
  error?: string;
}

export interface RoomNavigationResponse {
  current_room: string;
  available_rooms: string[];
  doorways: Doorway[];
  success: boolean;
  error?: string;
}

// Component prop types
export interface FloorPlanRendererProps {
  floorPlan: FloorPlan;
  assistant: Assistant;
  selectedObject?: string;
  viewport?: ViewportState;
  onObjectClick?: ObjectClickHandler;
  onPositionClick?: PositionClickHandler;
  onAssistantMove?: AssistantMoveHandler;
  onRoomChange?: RoomChangeHandler;
  className?: string;
  style?: React.CSSProperties;
}

export interface RoomSelectorProps {
  currentRoom: string;
  availableRooms: Room[];
  onRoomSelect: (roomId: string) => void;
  className?: string;
}

// Error types
export interface FloorPlanError {
  code: string;
  message: string;
  details?: any;
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type FloorPlanUpdate = DeepPartial<FloorPlan>;
export type AssistantUpdate = DeepPartial<Assistant>;

// Template types
export interface FloorPlanTemplate {
  id: string;
  name: string;
  description: string;
  category: FloorPlanCategory;
  preview_image?: string;
  template_data: FloorPlan;
}

export interface TemplateLibrary {
  templates: FloorPlanTemplate[];
  categories: FloorPlanCategory[];
  featured: string[]; // Template IDs
}