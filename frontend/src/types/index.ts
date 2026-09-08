export type LibraryKind = 'films' | 'cameras' | 'lenses';
export type LibraryItem = { id: number; name: string; created_at: string };
export type Library = Record<LibraryKind, LibraryItem[]>;
export type Status = 'shooting' | 'finished' | 'developed' | 'scanned' | 'archived';
export const statusLabels: Record<Status, string> = {shooting: '拍摄中', finished: '已拍完', developed: '已冲洗', scanned: '已扫描', archived: '已归档'};
export type Photo = {
  id: number; roll_id: number; frame_number: number; sort_order: number; url: string; thumbnail_url: string;
  width: number; height: number; file_size: number; original_filename: string; caption: string;
  is_cover: boolean; is_favorite: boolean;
};
export type ProcessRecord = {id: number; roll_id: number; [key: string]: string | number | null};
export type Roll = {
  id: number; roll_number: number; title: string; description: string; film_stock_id: number; camera_id: number;
  film_stock: string; camera: string; lenses: LibraryItem[]; shot_iso: number | null;
  started_at: string | null; finished_at: string | null; location: string; status: Status;
  expected_frames: number; actual_frames: number; cover_photo_id: number | null; created_at: string; updated_at: string;
  cover: Photo | null; is_favorite: boolean; photos: Photo[]; development: ProcessRecord | null; scan: ProcessRecord | null;
};
export type Usage = {name: string; count: number};
export type Stats = {total_rolls: number; total_photos: number; this_year: number; year: number; months: Usage[]; films: Usage[]; cameras: Usage[]; lenses: Usage[]; years: string[]};
export type Backup = {name: string; size: number};
