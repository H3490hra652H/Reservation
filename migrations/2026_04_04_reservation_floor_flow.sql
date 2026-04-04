ALTER TABLE menus
  ADD COLUMN IF NOT EXISTS has_options TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS has_seasoning TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS is_active TINYINT(1) NOT NULL DEFAULT 1;

ALTER TABLE reservations
  ADD COLUMN IF NOT EXISTS duration_minutes INT NOT NULL DEFAULT 120 AFTER reservation_datetime,
  ADD COLUMN IF NOT EXISTS status ENUM('pending','confirmed','occupied','completed','cancelled') NOT NULL DEFAULT 'confirmed' AFTER duration_minutes;

UPDATE reservations
SET duration_minutes = 120
WHERE duration_minutes IS NULL OR duration_minutes <= 0;

UPDATE reservations
SET status = 'confirmed'
WHERE status IS NULL OR TRIM(status) = '';

CREATE TABLE IF NOT EXISTS restaurant_tables (
  id INT AUTO_INCREMENT PRIMARY KEY,
  resource_code VARCHAR(80) NOT NULL,
  name VARCHAR(120) NOT NULL,
  table_label VARCHAR(30) NOT NULL,
  area VARCHAR(80) NOT NULL,
  sub_zone VARCHAR(80) NULL,
  x_position DECIMAL(8,2) NOT NULL DEFAULT 0,
  y_position DECIMAL(8,2) NOT NULL DEFAULT 0,
  width DECIMAL(8,2) NOT NULL DEFAULT 0,
  height DECIMAL(8,2) NOT NULL DEFAULT 0,
  radius DECIMAL(8,2) NOT NULL DEFAULT 0,
  shape ENUM('rect','round_rect','circle') NOT NULL DEFAULT 'round_rect',
  capacity INT NOT NULL DEFAULT 0,
  description TEXT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_restaurant_tables_resource_code (resource_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO restaurant_tables (
  resource_code, name, table_label, area, sub_zone,
  x_position, y_position, width, height, radius,
  shape, capacity, description, sort_order, is_active
) VALUES
  ('main-01','Meja 1','1','Ruang Utama','AC Front',188,122,108,58,18,'round_rect',4,'Dekat AC dan area live music.',10,1),
  ('main-02','Meja 2','2','Ruang Utama','AC Front',316,122,108,58,18,'round_rect',4,'Dekat AC dan area live music.',20,1),
  ('main-03','Meja 3','3','Ruang Utama','AC Front',444,122,108,58,18,'round_rect',4,'Dekat AC dan koridor tengah.',30,1),
  ('main-04','Meja 4','4','Ruang Utama','AC Front',572,122,108,58,18,'round_rect',4,'Dekat AC dan akses ke toilet.',40,1),
  ('main-11a','Meja 11A','11A','Ruang Utama','Left Window',76,226,106,54,18,'round_rect',2,'Sisi kiri dekat live music.',50,1),
  ('main-11b','Meja 11B','11B','Ruang Utama','Left Window',76,296,106,54,18,'round_rect',2,'Sisi kiri dekat jendela utama.',60,1),
  ('main-12a','Meja 12A','12A','Ruang Utama','Left Window',76,390,106,54,18,'round_rect',2,'Sisi kiri dekat koridor bar.',70,1),
  ('main-12b','Meja 12B','12B','Ruang Utama','Left Window',76,460,106,54,18,'round_rect',2,'Sisi kiri dekat bar dan waiting area.',80,1),
  ('main-05','Meja 5','5','Ruang Utama','Center Upper',320,228,98,52,16,'round_rect',2,'Tengah atas, dekat AC.',90,1),
  ('main-05b','Meja 5B','5B','Ruang Utama','Center Upper',438,228,98,52,16,'round_rect',2,'Tengah atas, pasangan Meja 5.',100,1),
  ('main-06','Meja 6','6','Ruang Utama','Center Upper',556,228,98,52,16,'round_rect',2,'Tengah atas, dekat toilet.',110,1),
  ('main-06b','Meja 6B','6B','Ruang Utama','Center Upper',674,228,98,52,16,'round_rect',2,'Tengah atas, akses dekat wastafel.',120,1),
  ('main-07','Meja 7','7','Ruang Utama','Center Main',382,372,74,74,37,'circle',4,'Area tengah utama.',130,1),
  ('main-08','Meja 8','8','Ruang Utama','Center Main',494,372,74,74,37,'circle',4,'Area tengah utama.',140,1),
  ('main-08b','Meja 8B','8B','Ruang Utama','Center Main',606,372,74,74,37,'circle',4,'Area tengah utama, dekat sofa.',150,1),
  ('main-09','Meja 9','9','Ruang Utama','Center Main',718,372,74,74,37,'circle',4,'Tengah kanan dekat sofa.',160,1),
  ('main-10','Meja 10','10','Ruang Utama','Center Lower',468,498,108,56,18,'round_rect',4,'Tengah bawah dekat kasir.',170,1),
  ('main-10b','Meja 10B','10B','Ruang Utama','Center Lower',602,498,108,56,18,'round_rect',4,'Tengah bawah dekat sofa/waiting area.',180,1)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  table_label = VALUES(table_label),
  area = VALUES(area),
  sub_zone = VALUES(sub_zone),
  x_position = VALUES(x_position),
  y_position = VALUES(y_position),
  width = VALUES(width),
  height = VALUES(height),
  radius = VALUES(radius),
  shape = VALUES(shape),
  capacity = VALUES(capacity),
  description = VALUES(description),
  sort_order = VALUES(sort_order),
  is_active = VALUES(is_active);
