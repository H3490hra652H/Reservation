-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 10, 2026 at 05:44 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `moca_restaurant`
--

-- --------------------------------------------------------

--
-- Table structure for table `daily_menu_stock`
--

CREATE TABLE `daily_menu_stock` (
  `id` int(11) NOT NULL,
  `menu_id` int(11) DEFAULT NULL,
  `status` enum('ready','pending','out') DEFAULT 'out',
  `stock_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `daily_menu_stock`
--

INSERT INTO `daily_menu_stock` (`id`, `menu_id`, `status`, `stock_date`) VALUES
(6846, 0, 'ready', '2026-03-10'),
(6847, 18, 'ready', '2026-03-10'),
(6848, 19, 'ready', '2026-03-10'),
(6849, 20, 'ready', '2026-03-10'),
(6850, 21, 'ready', '2026-03-10'),
(6851, 22, 'ready', '2026-03-10'),
(6852, 23, 'ready', '2026-03-10'),
(6853, 24, 'ready', '2026-03-10'),
(6854, 25, 'ready', '2026-03-10'),
(6855, 26, 'ready', '2026-03-10'),
(6856, 27, 'ready', '2026-03-10'),
(6857, 28, 'ready', '2026-03-10'),
(6858, 29, 'ready', '2026-03-10'),
(6859, 30, 'ready', '2026-03-10'),
(6860, 31, 'ready', '2026-03-10'),
(6861, 32, 'ready', '2026-03-10'),
(6862, 33, 'ready', '2026-03-10'),
(6863, 34, 'ready', '2026-03-10'),
(6864, 35, 'ready', '2026-03-10'),
(6865, 36, 'ready', '2026-03-10'),
(6866, 37, 'ready', '2026-03-10'),
(6867, 38, 'ready', '2026-03-10'),
(6868, 39, 'ready', '2026-03-10'),
(6869, 40, 'ready', '2026-03-10'),
(6870, 41, 'ready', '2026-03-10'),
(6871, 42, 'ready', '2026-03-10'),
(6872, 43, 'ready', '2026-03-10'),
(6873, 44, 'ready', '2026-03-10'),
(6874, 45, 'ready', '2026-03-10'),
(6875, 46, 'ready', '2026-03-10'),
(6876, 47, '', '2026-03-10'),
(6877, 48, 'ready', '2026-03-10'),
(6878, 49, 'ready', '2026-03-10'),
(6879, 50, 'ready', '2026-03-10'),
(6880, 51, 'ready', '2026-03-10'),
(6881, 52, 'ready', '2026-03-10'),
(6882, 53, 'ready', '2026-03-10'),
(6883, 54, 'ready', '2026-03-10'),
(6884, 55, 'ready', '2026-03-10'),
(6885, 56, 'ready', '2026-03-10'),
(6886, 57, 'ready', '2026-03-10'),
(6887, 58, 'ready', '2026-03-10'),
(6888, 59, 'ready', '2026-03-10'),
(6889, 60, 'ready', '2026-03-10'),
(6890, 61, 'ready', '2026-03-10'),
(6891, 62, 'ready', '2026-03-10'),
(6892, 63, 'ready', '2026-03-10'),
(6893, 64, 'ready', '2026-03-10'),
(6894, 65, 'ready', '2026-03-10'),
(6895, 75, 'ready', '2026-03-10'),
(6896, 76, 'ready', '2026-03-10'),
(6897, 77, 'ready', '2026-03-10'),
(6898, 78, 'ready', '2026-03-10'),
(6899, 79, 'ready', '2026-03-10'),
(6900, 80, 'ready', '2026-03-10'),
(6901, 81, 'ready', '2026-03-10'),
(6902, 82, 'ready', '2026-03-10'),
(6903, 91, 'ready', '2026-03-10'),
(6904, 96, 'ready', '2026-03-10'),
(6905, 97, 'ready', '2026-03-10'),
(6906, 98, 'ready', '2026-03-10'),
(6907, 99, 'ready', '2026-03-10'),
(6908, 100, 'ready', '2026-03-10'),
(6909, 101, 'ready', '2026-03-10'),
(6910, 102, 'ready', '2026-03-10'),
(6911, 103, 'ready', '2026-03-10'),
(6912, 104, 'ready', '2026-03-10'),
(6913, 105, 'ready', '2026-03-10'),
(6914, 106, 'ready', '2026-03-10'),
(6915, 107, 'ready', '2026-03-10'),
(6916, 108, 'ready', '2026-03-10'),
(6917, 109, 'ready', '2026-03-10'),
(6918, 110, 'ready', '2026-03-10'),
(6919, 111, 'ready', '2026-03-10'),
(6920, 112, 'ready', '2026-03-10'),
(6921, 113, 'ready', '2026-03-10'),
(6922, 114, 'ready', '2026-03-10'),
(6923, 115, 'ready', '2026-03-10'),
(6924, 116, 'ready', '2026-03-10'),
(6925, 117, 'ready', '2026-03-10'),
(6926, 118, 'ready', '2026-03-10'),
(6927, 119, 'ready', '2026-03-10'),
(6928, 120, 'ready', '2026-03-10'),
(6929, 121, 'ready', '2026-03-10'),
(6930, 122, 'ready', '2026-03-10'),
(6931, 123, 'ready', '2026-03-10'),
(6932, 124, 'ready', '2026-03-10'),
(6933, 125, 'ready', '2026-03-10'),
(6934, 126, 'ready', '2026-03-10'),
(6935, 127, 'ready', '2026-03-10'),
(6936, 128, 'ready', '2026-03-10'),
(6937, 129, 'ready', '2026-03-10'),
(6938, 130, 'ready', '2026-03-10'),
(6939, 131, 'ready', '2026-03-10'),
(6940, 132, 'ready', '2026-03-10'),
(6941, 133, 'ready', '2026-03-10'),
(6942, 134, 'ready', '2026-03-10'),
(6943, 135, 'ready', '2026-03-10'),
(6944, 136, 'ready', '2026-03-10'),
(6945, 137, 'ready', '2026-03-10'),
(6946, 138, 'ready', '2026-03-10'),
(6947, 139, 'ready', '2026-03-10'),
(6948, 140, 'ready', '2026-03-10'),
(6949, 141, 'ready', '2026-03-10'),
(6950, 142, 'ready', '2026-03-10'),
(6951, 143, 'ready', '2026-03-10'),
(6952, 144, 'ready', '2026-03-10'),
(6953, 145, 'ready', '2026-03-10'),
(6954, 146, 'ready', '2026-03-10'),
(6955, 147, 'ready', '2026-03-10'),
(6956, 148, 'ready', '2026-03-10'),
(6957, 149, 'ready', '2026-03-10'),
(6958, 150, 'ready', '2026-03-10'),
(6959, 151, 'ready', '2026-03-10'),
(6960, 152, 'ready', '2026-03-10'),
(6961, 153, 'ready', '2026-03-10'),
(6962, 154, 'ready', '2026-03-10'),
(6963, 155, 'ready', '2026-03-10'),
(6964, 156, 'ready', '2026-03-10'),
(6965, 157, 'ready', '2026-03-10'),
(6966, 158, 'ready', '2026-03-10'),
(6967, 159, 'ready', '2026-03-10'),
(6968, 160, 'ready', '2026-03-10'),
(6969, 161, 'ready', '2026-03-10'),
(6970, 162, 'ready', '2026-03-10'),
(6971, 163, 'ready', '2026-03-10'),
(6972, 164, 'ready', '2026-03-10'),
(6973, 165, 'ready', '2026-03-10'),
(6974, 166, 'ready', '2026-03-10'),
(6975, 167, 'ready', '2026-03-10'),
(6976, 168, 'ready', '2026-03-10'),
(6977, 179, 'ready', '2026-03-10'),
(6978, 180, 'ready', '2026-03-10'),
(6979, 181, 'ready', '2026-03-10'),
(6980, 193, 'ready', '2026-03-10'),
(6981, 194, 'ready', '2026-03-10'),
(7163, 89, 'ready', '2026-03-10'),
(7164, 90, 'ready', '2026-03-10'),
(7165, 95, 'ready', '2026-03-10'),
(7166, 88, 'ready', '2026-03-10'),
(7167, 92, 'ready', '2026-03-10'),
(7168, 93, 'ready', '2026-03-10'),
(7169, 94, 'ready', '2026-03-10');

-- --------------------------------------------------------

--
-- Table structure for table `fish_size_prices`
--

CREATE TABLE `fish_size_prices` (
  `size_category` enum('kecil','sedang','besar','jumbo','super_jumbo') NOT NULL,
  `price` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fish_size_prices`
--

INSERT INTO `fish_size_prices` (`size_category`, `price`) VALUES
('kecil', 40000),
('sedang', 45000),
('besar', 50000),
('jumbo', 55000),
('super_jumbo', 60000);

-- --------------------------------------------------------

--
-- Table structure for table `fish_stock`
--

CREATE TABLE `fish_stock` (
  `id` int(11) NOT NULL,
  `fish_type_id` int(11) DEFAULT NULL,
  `weight_ons` decimal(4,1) DEFAULT NULL,
  `fish_count` int(11) DEFAULT NULL,
  `size_category` enum('kecil','sedang','besar','jumbo','super_jumbo') DEFAULT NULL,
  `status` enum('ready','not_ready') DEFAULT 'ready',
  `stock_date` date DEFAULT NULL,
  `price` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Triggers `fish_stock`
--
DELIMITER $$
CREATE TRIGGER `fish_price_insert` BEFORE INSERT ON `fish_stock` FOR EACH ROW BEGIN

IF NEW.weight_ons IS NOT NULL THEN

SET NEW.price = NEW.weight_ons * 10 * 18500;

ELSE

SET NEW.price = (
SELECT price
FROM fish_size_prices
WHERE size_category = NEW.size_category
);

END IF;

END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `fish_types`
--

CREATE TABLE `fish_types` (
  `id` int(11) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `fish_category` enum('sea','nila') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fish_types`
--

INSERT INTO `fish_types` (`id`, `name`, `fish_category`) VALUES
(1, 'kakap', 'sea'),
(2, 'goropa', 'sea'),
(3, 'bobara', 'sea'),
(4, 'nila', 'nila');

-- --------------------------------------------------------

--
-- Table structure for table `menus`
--

CREATE TABLE `menus` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `category` enum('ayam','ikan tuna','daging','nasi','mie','soup','side','snack','dessert','drink','ikan laut','ikan nila','kepiting','sayuran','chilin','koffie','nokoffie','udang','cumi') DEFAULT NULL,
  `serving_type` enum('pcs','paket','porsi','dish') DEFAULT NULL,
  `stock_type` enum('normal','weight','size') DEFAULT 'normal',
  `divisi` enum('bakar','bakar/local','bakar/seafood','seafood','jus','bar','local','taiwan_snack','plating') NOT NULL,
  `price` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `menus`
--

INSERT INTO `menus` (`id`, `name`, `category`, `serving_type`, `stock_type`, `divisi`, `price`) VALUES
(0, 'Chicken Skin', 'chilin', 'paket', 'normal', 'taiwan_snack', 23000),
(1, 'Ikan Bakar Biasa', 'ikan laut', 'porsi', 'weight', 'bakar', 18500),
(2, 'Ikan Bakar Rica', 'ikan laut', 'porsi', 'weight', 'bakar', 18500),
(3, 'Ikan Bakar Kecap', 'ikan laut', 'porsi', 'weight', 'bakar', 18500),
(4, 'Ikan Goreng Kering', 'ikan laut', 'porsi', 'weight', 'bakar/seafood', 18500),
(5, 'Ikan Goreng Rica Spesial', 'ikan laut', 'porsi', 'weight', 'bakar/seafood', 18500),
(6, 'Ikan Steam Kecap Rica', 'ikan laut', 'porsi', 'weight', 'bakar/seafood', 18500),
(7, 'Ikan Steam Bawang Putih', 'ikan laut', 'porsi', 'weight', 'bakar/seafood', 18500),
(8, 'Ikan Asam Manis', 'ikan laut', 'porsi', 'weight', 'bakar/seafood', 18500),
(9, 'Ikan Woku', 'ikan laut', 'porsi', 'weight', 'bakar/local', 18500),
(10, 'Kuah Asam Gorontalo', 'ikan laut', 'porsi', 'weight', 'bakar/local', 18500),
(11, 'Nila Bakar', 'ikan nila', 'porsi', 'size', 'bakar', NULL),
(12, 'Nila Bakar Rica', 'ikan nila', 'porsi', 'size', 'bakar', NULL),
(13, 'Nila Goreng', 'ikan nila', 'porsi', 'size', 'bakar/seafood', NULL),
(14, 'Nila Kuah Asam', 'ikan nila', 'porsi', 'size', 'bakar/local', NULL),
(15, 'Nila Steam kecap rica', 'ikan nila', 'porsi', 'size', 'bakar/seafood', NULL),
(16, 'Nila Woku', 'ikan nila', 'porsi', 'size', 'bakar/local', NULL),
(17, 'Nila Asam Manis', 'ikan nila', 'porsi', 'size', 'bakar/seafood', NULL),
(18, 'Ayam Geprek', 'ayam', 'pcs', 'normal', 'local', 20000),
(19, 'Ayam Geprek', 'ayam', 'paket', 'normal', 'local', 25000),
(20, 'Ayam Crispy', 'ayam', 'pcs', 'normal', 'local', 20000),
(21, 'Ayam Crispy', 'ayam', 'paket', 'normal', 'local', 0),
(22, 'Ayam Kalasan', 'ayam', 'pcs', 'normal', 'local', 28500),
(23, 'Ayam Kalasan', 'ayam', 'paket', 'normal', 'local', 35000),
(24, 'Ayam Bakar Iloni', 'ayam', 'pcs', 'normal', 'bakar', 28500),
(25, 'Ayam Bakar Iloni', 'ayam', 'paket', 'normal', 'bakar', 35000),
(26, 'Ayam Bakar Rica', 'ayam', 'pcs', 'normal', 'bakar', 28500),
(27, 'Ayam Bakar Rica', 'ayam', 'paket', 'normal', 'bakar', 35000),
(28, 'Ayam Bakar Kecap', 'ayam', 'pcs', 'normal', 'bakar', 28500),
(29, 'Ayam Bakar Kecap', 'ayam', 'paket', 'normal', 'bakar', 35000),
(30, 'Ayam Serundeng Manna', 'ayam', 'pcs', 'normal', 'local', 30500),
(31, 'Ayam Serundeng Manna', 'ayam', 'paket', 'normal', 'local', 37500),
(32, 'Sate Ayam (6 Tusuk)', 'ayam', 'porsi', 'normal', 'bakar', 27500),
(33, 'Ayam Goreng Kecap', 'ayam', 'porsi', 'normal', 'local', 28500),
(34, 'Ayam Sambal Matah', 'ayam', 'porsi', 'normal', 'local', 28500),
(35, 'Ayam Bumbu RW', 'ayam', 'porsi', 'normal', 'local', 29500),
(36, 'Ayam Goreng Mentega', 'ayam', 'porsi', 'normal', 'seafood', 35000),
(37, 'Ayam Asam Manis', 'ayam', 'porsi', 'normal', 'seafood', 35000),
(38, 'Ayam Telur Asin', 'ayam', 'porsi', 'normal', 'seafood', 37500),
(39, 'Sate Tuna (5 Tusuk)', 'ikan tuna', 'porsi', 'normal', 'bakar', 25000),
(40, 'Dada Tuna Goreng', 'ikan tuna', 'pcs', 'normal', 'bakar/seafood', 25000),
(41, 'Paket Dada Tuna goreng', 'ikan tuna', 'paket', 'normal', 'bakar/seafood', 35000),
(42, 'Paket Tuna Bakar Rica', 'ikan tuna', 'paket', 'normal', 'bakar', 35000),
(247, 'Paket Tuna Goreng Rica', 'ikan tuna', 'paket', 'normal', 'seafood', 35000),
(43, 'Tuna Fillet Asam Manis', 'ikan tuna', 'porsi', 'normal', 'seafood', 35000),
(44, 'Tuna Woku', 'ikan tuna', 'porsi', 'normal', 'local', 35000),
(45, 'Tuna Garo Rica', 'ikan tuna', 'porsi', 'normal', 'local', 30000),
(46, 'Paket Rahang Tuna', 'ikan tuna', 'paket', 'normal', 'bakar', 45000),
(47, 'Rahang Tuna', 'ikan tuna', 'pcs', 'weight', 'bakar', 45000),
(48, 'Sapi Lada Hitam', 'daging', 'porsi', 'normal', 'seafood', 40000),
(49, 'Sate Daging (5 Tusuk)', 'daging', 'porsi', 'normal', 'bakar', 40000),
(50, 'Daging Sambal Goreng', 'daging', 'porsi', 'normal', 'local', 40000),
(51, 'Daging Bakar Balanga', 'daging', 'porsi', 'normal', 'local', 40000),
(52, 'Daging Sate Garo', 'daging', 'porsi', 'normal', 'local', 40000),
(53, 'Udang Sambal Pete', 'udang', 'porsi', 'normal', 'local', 25000),
(54, 'Udang Tempura', 'udang', 'porsi', 'normal', 'seafood', 35000),
(55, 'Udang Goreng Tepung', 'udang', 'porsi', 'normal', 'seafood', 35000),
(56, 'Udang Goreng Mentega', 'udang', 'porsi', 'normal', 'seafood', 40000),
(57, 'Udang Asam Manis', 'udang', 'porsi', 'normal', 'seafood', 40000),
(58, 'Udang Saus Pedas', 'udang', 'porsi', 'normal', 'seafood', 40000),
(59, 'Udang Balado', 'udang', 'porsi', 'normal', 'seafood', 40000),
(60, 'Udang Telur Asin', 'udang', 'porsi', 'normal', 'seafood', 45000),
(61, 'Cumi Bakar Rica', 'cumi', 'porsi', 'normal', 'bakar', 35000),
(62, 'Cumi Goreng Tepung', 'cumi', 'porsi', 'normal', 'seafood', 35000),
(63, 'Cumi Goreng Mentega', 'cumi', 'porsi', 'normal', 'seafood', 40000),
(64, 'Cumi Asam Manis', 'cumi', 'porsi', 'normal', 'seafood', 40000),
(65, 'Cumi Saus Pedas', 'cumi', 'porsi', 'normal', 'seafood', 40000),
(66, 'Telur', 'side', 'pcs', 'normal', 'local', 5000),
(67, 'Extra Sambal', 'side', 'pcs', 'normal', 'local', 6000),
(68, 'Extra Serundeng', 'side', 'pcs', 'normal', 'local', 7000),
(69, 'Tempe Goreng Crispy', 'side', 'porsi', 'normal', 'seafood', 20000),
(70, 'Tahu Goreng Crispy', 'side', 'porsi', 'normal', 'seafood', 20000),
(248, 'Tahu/Tempe Goreng Crispy', 'side', 'porsi', 'normal', 'seafood', 20000),
(71, 'Ati Ampela Goreng', 'side', 'porsi', 'normal', 'local', 25000),
(72, 'Perkedel Nike', 'side', 'porsi', 'normal', 'local', 22500),
(73, 'Fuyunghai', 'side', 'porsi', 'normal', 'seafood', 30000),
(74, 'Tahu Spesial Manna', 'side', 'porsi', 'normal', 'seafood', 35000),
(75, 'Nasi Putih', 'nasi', 'porsi', 'normal', 'plating', 8000),
(76, 'Nasi Pecel', 'nasi', 'porsi', 'normal', 'local', 25000),
(77, 'Nasi Goreng Kampung', 'nasi', 'porsi', 'normal', 'seafood', 27500),
(78, 'Nasi Goreng Sagela', 'nasi', 'porsi', 'normal', 'seafood', 27500),
(79, 'Nasi Goreng Spesial', 'nasi', 'porsi', 'normal', 'seafood', 30000),
(80, 'Nasi Goreng Pete', 'nasi', 'porsi', 'normal', 'seafood', 30000),
(81, 'Bubur Manado', 'nasi', 'porsi', 'normal', 'local', 23000),
(82, 'Bubur Ayam', 'nasi', 'porsi', 'normal', 'local', 23000),
(83, 'Mie Cakalang', 'mie', 'porsi', 'normal', 'local', 25000),
(84, 'Mie Ayam Spesial', 'mie', 'porsi', 'normal', 'local', 28000),
(85, 'Mie Goreng Spesial', 'mie', 'porsi', 'normal', 'seafood', 30000),
(86, 'Mie Titi', 'mie', 'porsi', 'normal', 'seafood', 30000),
(87, 'Bihun Goreng', 'mie', 'porsi', 'normal', 'seafood', 30000),
(88, 'Kuah Kaldu Telur', 'soup', 'porsi', 'normal', 'local', 12000),
(89, 'Bakso Kuah', 'soup', 'porsi', 'normal', 'local', 25000),
(90, 'Bakso Kuah Komplit', 'soup', 'porsi', 'normal', 'local', 30000),
(91, 'Capcay Seafood', 'sayuran', 'porsi', 'normal', 'seafood', 35000),
(92, 'Sapo Tahu', 'soup', 'porsi', 'normal', 'seafood', 38500),
(93, 'Sup Asparagus', 'soup', 'porsi', 'normal', 'seafood', 40000),
(94, 'Tom Yum Seafood', 'soup', 'porsi', 'normal', 'seafood', 45000),
(95, 'Dumpling Soup', 'soup', 'porsi', 'normal', 'local', 25000),
(96, 'Kangkung Cah', 'sayuran', 'porsi', 'normal', 'local', 18000),
(97, 'Kangkung Terasi', 'sayuran', 'porsi', 'normal', 'local', 20000),
(98, 'Sayur Pecel', 'sayuran', 'porsi', 'normal', 'local', 20000),
(99, 'Kacang Panjang Terasi', 'sayuran', 'porsi', 'normal', 'local', 22500),
(100, 'Taoge Ikan Asin', 'sayuran', 'porsi', 'normal', 'local', 22500),
(101, 'Kangkung Bunga Pepaya', 'sayuran', 'porsi', 'normal', 'local', 22500),
(102, 'Goroho Stick', 'snack', 'porsi', 'normal', 'local', 20000),
(103, 'Goroho gulmer', 'snack', 'porsi', 'normal', 'local', 25000),
(104, 'Tahu Goreng BBQ', 'snack', 'porsi', 'normal', 'local', 20000),
(105, 'Kentang Goreng', 'snack', 'porsi', 'normal', 'local', 20000),
(106, 'Pisang Goreng Raja', 'snack', 'porsi', 'normal', 'local', 20000),
(107, 'Pisang Goreng Pagata', 'snack', 'porsi', 'normal', 'local', 20000),
(108, 'Pangsit Goreng', 'snack', 'porsi', 'normal', 'local', 25000),
(109, 'Mandu Korean Dumpling', 'snack', 'porsi', 'normal', 'local', 25000),
(110, 'Bakso Udang Ayam', 'snack', 'porsi', 'normal', 'local', 25000),
(111, 'Pisang Palm Cheese', 'snack', 'porsi', 'normal', 'local', 30000),
(112, 'Ubi Thailand', 'snack', 'porsi', 'normal', 'local', 25000),
(113, 'Es Serut Kacang Susu Gulmer', 'dessert', 'porsi', 'normal', 'jus', 18000),
(114, 'Es Serut Kacang Susu Sirup', 'dessert', 'porsi', 'normal', 'jus', 18000),
(115, 'Es Kacang Ijo', 'dessert', 'porsi', 'normal', 'jus', 20000),
(116, 'Es Cendol', 'dessert', 'porsi', 'normal', 'jus', 20000),
(117, 'Es Kopi Cendol', 'dessert', 'porsi', 'normal', 'jus', 25000),
(118, 'Es Palubutung', 'dessert', 'porsi', 'normal', 'jus', 25000),
(119, 'Es Campur Manna', 'dessert', 'porsi', 'normal', 'jus', 25000),
(120, 'Es Brenebon Durian', 'dessert', 'porsi', 'normal', 'jus', 27500),
(121, 'Avocado Float', 'dessert', 'porsi', 'normal', 'jus', 27500),
(122, 'Choco Strawnerry Toast', 'dessert', 'porsi', 'normal', 'jus', 22000),
(123, 'Ice Cream Puff', 'dessert', 'porsi', 'normal', 'jus', 20000),
(124, 'Braffle', 'dessert', 'porsi', 'normal', 'jus', 18000),
(125, 'Jus Buah Naga', 'dessert', 'porsi', 'normal', 'jus', 25000),
(126, 'Jus Buah Sirsak', 'dessert', 'porsi', 'normal', 'jus', 25000),
(127, 'Jus Buah Avocado', 'dessert', 'porsi', 'normal', 'jus', 25000),
(128, 'Jus Buah Durian', 'dessert', 'porsi', 'normal', 'jus', 30000),
(129, 'Air Mineral Kecil', 'drink', 'pcs', 'normal', 'bar', 4000),
(130, 'Air Mineral Tanggung', 'drink', 'pcs', 'normal', 'bar', 8000),
(131, 'Teh Tawar', 'drink', 'pcs', 'normal', 'bar', 8000),
(132, 'Teh Manis', 'drink', 'pcs', 'normal', 'bar', 10000),
(133, 'Kopi Tubruk', 'drink', 'pcs', 'normal', 'bar', 12000),
(134, 'Kopi Tubruk Susu', 'drink', 'pcs', 'normal', 'bar', 15000),
(135, 'Kopi Hitam', 'drink', 'pcs', 'normal', 'bar', 15000),
(136, 'Kopi Susu', 'drink', 'pcs', 'normal', 'bar', 18000),
(137, 'Es Kopi Shakerato', 'drink', 'pcs', 'normal', 'bar', 20000),
(138, 'Jeruk Nipis', 'drink', 'pcs', 'normal', 'bar', 12000),
(139, 'Jeruk Manis', 'drink', 'pcs', 'normal', 'bar', 18000),
(140, 'Lemon Tea', 'drink', 'pcs', 'normal', 'bar', 20000),
(141, 'Coklat Panas', 'drink', 'pcs', 'normal', 'bar', 27500),
(142, 'Brown Sugar Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 22000),
(143, 'Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 18000),
(144, 'Chocolade Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 25000),
(145, 'Pandan Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 20000),
(146, 'Krispy Caramel Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 25000),
(147, 'Salted Caramel Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 27000),
(148, 'Choco Hazelnut Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 23000),
(149, 'Choco Jelly Koffie Latte', 'koffie', 'pcs', 'normal', 'bar', 23000),
(150, 'Honey Long Black', 'koffie', 'pcs', 'normal', 'bar', 22000),
(151, 'Taro Latte', 'nokoffie', 'pcs', 'normal', 'bar', 20000),
(152, 'Red Velvet Latte', 'nokoffie', 'pcs', 'normal', 'bar', 20000),
(153, 'Coconut Matcha Cloud', 'nokoffie', 'pcs', 'normal', 'bar', 23000),
(154, 'Biscuit Melk', 'nokoffie', 'pcs', 'normal', 'bar', 23000),
(155, 'Royal Chocolade', 'nokoffie', 'pcs', 'normal', 'bar', 26000),
(156, 'Thai Tea', 'nokoffie', 'pcs', 'normal', 'bar', 20000),
(157, 'Sour Rosie', 'nokoffie', 'pcs', 'normal', 'bar', 23000),
(158, 'Green Tea latte', 'nokoffie', 'pcs', 'normal', 'bar', 23000),
(159, 'Big Fried Chicken Original small', 'chilin', 'porsi', 'normal', 'taiwan_snack', 20000),
(160, 'Big Fried Chicken Original large', 'chilin', 'porsi', 'normal', 'taiwan_snack', 25000),
(161, 'Big Fried Chicken Bubble small', 'chilin', 'porsi', 'normal', 'taiwan_snack', 23000),
(162, 'Big Fried Chicken Bubble large', 'chilin', 'porsi', 'normal', 'taiwan_snack', NULL),
(163, 'Big Fried Chicken Original small + topping', 'chilin', 'porsi', 'normal', 'taiwan_snack', 27000),
(164, 'Big Fried Chicken Original large + topping', 'chilin', 'porsi', 'normal', 'taiwan_snack', 32000),
(165, 'Big Fried Chicken Bubble small + topping', 'chilin', 'porsi', 'normal', 'taiwan_snack', 30000),
(166, 'Big Fried Chicken Bubble large + topping', 'chilin', 'porsi', 'normal', 'taiwan_snack', 35000),
(167, 'Ayam Ori chilin + nasi + topping', 'chilin', 'paket', 'normal', 'taiwan_snack', 28000),
(168, 'Ayam Bubble Chilin + nasi + topping', 'chilin', 'paket', 'normal', 'taiwan_snack', 28000),
(179, 'Japanese Curry', 'chilin', 'paket', 'normal', 'taiwan_snack', 30000),
(180, 'Salted Egg Chicken', 'chilin', 'paket', 'normal', 'taiwan_snack', 37000),
(181, 'Salted Egg Chicken Skin', 'chilin', 'paket', 'normal', 'taiwan_snack', 30000),
(192, 'nila bilendango', 'ikan nila', 'porsi', 'size', 'local', NULL),
(193, 'dada tuna bakar', 'ikan tuna', 'pcs', 'normal', 'bakar', 25000),
(194, 'paket dada tuna bakar', 'ikan tuna', 'paket', 'normal', 'bakar', 35000),
(197, 'es cendol durian', 'dessert', 'pcs', 'normal', 'jus', 25000),
(200, 'nutrisari dingin', 'drink', 'pcs', 'normal', 'bar', 12000),
(201, 'Air Mineral Kecil Panas', 'drink', 'pcs', 'normal', 'bar', 4000),
(202, 'Air Mineral Tanggung Panas', 'drink', 'pcs', 'normal', 'bar', 8000),
(203, 'Teh Tawar Panas', 'drink', 'pcs', 'normal', 'bar', 8000),
(204, 'Teh Manis Panas', 'drink', 'pcs', 'normal', 'bar', 10000),
(205, 'Kopi Tubruk Panas', 'drink', 'pcs', 'normal', 'bar', 12000),
(206, 'Kopi Tubruk Susu Panas', 'drink', 'pcs', 'normal', 'bar', 15000),
(207, 'Kopi Hitam Panas', 'drink', 'pcs', 'normal', 'bar', 15000),
(208, 'Kopi Susu Panas', 'drink', 'pcs', 'normal', 'bar', 18000),
(209, 'Es Kopi Shakerato Panas', 'drink', 'pcs', 'normal', 'bar', 20000),
(210, 'Jeruk Nipis Panas', 'drink', 'pcs', 'normal', 'bar', 12000),
(211, 'Jeruk Manis Panas', 'drink', 'pcs', 'normal', 'bar', 18000),
(212, 'Lemon Tea Panas', 'drink', 'pcs', 'normal', 'bar', 20000),
(213, 'Coklat Panas Panas', 'drink', 'pcs', 'normal', 'bar', 27500),
(214, 'nutrisari Panas', 'drink', 'pcs', 'normal', 'bar', 12000),
(216, 'Air Mineral Kecil Dingin', 'drink', 'pcs', 'normal', 'bar', 4000),
(217, 'Air Mineral Tanggung Dingin', 'drink', 'pcs', 'normal', 'bar', 8000),
(218, 'Teh Tawar Dingin', 'drink', 'pcs', 'normal', 'bar', 8000),
(219, 'Teh Manis Dingin', 'drink', 'pcs', 'normal', 'bar', 10000),
(220, 'Kopi Tubruk Dingin', 'drink', 'pcs', 'normal', 'bar', 12000),
(221, 'Kopi Tubruk Susu Dingin', 'drink', 'pcs', 'normal', 'bar', 15000),
(222, 'Kopi Hitam Dingin', 'drink', 'pcs', 'normal', 'bar', 15000),
(223, 'Kopi Susu Dingin', 'drink', 'pcs', 'normal', 'bar', 18000),
(224, 'Es Kopi Shakerato Dingin', 'drink', 'pcs', 'normal', 'bar', 20000),
(225, 'Jeruk Nipis Dingin', 'drink', 'pcs', 'normal', 'bar', 12000),
(226, 'Jeruk Manis Dingin', 'drink', 'pcs', 'normal', 'bar', 18000),
(227, 'Lemon Tea Dingin', 'drink', 'pcs', 'normal', 'bar', 20000),
(228, 'Coklat Panas ', 'drink', 'pcs', 'normal', 'bar', 27500),
(229, 'nutrisari Dingin', 'drink', 'pcs', 'normal', 'bar', 12000);

-- --------------------------------------------------------

--
-- Table structure for table `reservations`
--

CREATE TABLE `reservations` (
  `id` int(11) NOT NULL,
  `customer_name` varchar(255) DEFAULT NULL,
  `table_number` varchar(20) DEFAULT NULL,
  `people_count` int(11) DEFAULT NULL,
  `reservation_datetime` datetime DEFAULT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reservations`
--

INSERT INTO `reservations` (`id`, `customer_name`, `table_number`, `people_count`, `reservation_datetime`, `description`) VALUES
(14, 'BEBY SEPTIVIANSYAH', '11 + 2 kursi', 6, '2026-03-10 13:38:00', 'bukber'),
(15, 'Mia', '12', 3, '2026-03-10 13:42:00', 'bukber'),
(16, 'sintia kau', 'meja makan outdoor', 20, '2026-03-10 13:45:00', 'bukber'),
(17, 'vemas', '1-4', 50, '2026-03-10 20:54:00', '');

-- --------------------------------------------------------

--
-- Table structure for table `reservation_items`
--

CREATE TABLE `reservation_items` (
  `id` int(11) NOT NULL,
  `reservation_id` int(11) DEFAULT NULL,
  `menu_id` int(11) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `special_request` enum('no_special','with_special') DEFAULT 'no_special',
  `dish_description` text DEFAULT NULL,
  `fish_type` varchar(20) DEFAULT NULL,
  `fish_size` varchar(20) DEFAULT NULL,
  `fish_weight` decimal(5,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reservation_items`
--

INSERT INTO `reservation_items` (`id`, `reservation_id`, `menu_id`, `quantity`, `special_request`, `dish_description`, `fish_type`, `fish_size`, `fish_weight`) VALUES
(67, 14, 77, 1, NULL, '', NULL, '', 0.00),
(68, 14, 83, 1, NULL, '', NULL, '', 0.00),
(69, 14, 57, 1, NULL, '', NULL, '', 0.00),
(70, 14, 75, 1, NULL, '', NULL, '', 0.00),
(71, 14, 19, 1, NULL, '', NULL, '', 0.00),
(72, 14, 81, 1, NULL, '', NULL, '', 0.00),
(73, 14, 82, 1, NULL, '', NULL, '', 0.00),
(74, 14, 218, 1, NULL, '', NULL, '', 0.00),
(75, 14, 130, 3, NULL, '', NULL, '', 0.00),
(76, 14, 116, 1, NULL, '', NULL, '', 0.00),
(77, 14, 118, 1, NULL, '', NULL, '', 0.00),
(78, 14, 197, 1, NULL, '', NULL, '', 0.00),
(79, 14, 124, 1, NULL, '', NULL, '', 0.00),
(80, 14, 115, 1, NULL, '', NULL, '', 0.00),
(81, 15, 64, 1, NULL, '', NULL, '', 0.00),
(82, 15, 75, 1, NULL, '', NULL, '', 0.00),
(83, 15, 219, 1, NULL, '', NULL, '', 0.00),
(84, 15, 92, 1, NULL, '', NULL, '', 0.00),
(85, 15, 200, 1, NULL, '', NULL, '', 0.00),
(86, 15, 34, 1, NULL, '', NULL, '', 0.00),
(87, 15, 217, 1, NULL, '', NULL, '', 0.00),
(88, 16, 17, 1, NULL, '', NULL, 'kecil', 0.00),
(89, 16, 91, 1, NULL, '', NULL, '', 0.00),
(90, 16, 116, 1, NULL, '', NULL, '', 0.00),
(91, 16, 75, 1, NULL, '', NULL, '', 0.00),
(92, 16, 76, 1, NULL, '', NULL, '', 0.00),
(93, 16, 32, 1, NULL, '', NULL, '', 0.00),
(94, 16, 130, 1, NULL, '', NULL, '', 0.00),
(95, 16, 64, 1, NULL, '', NULL, '', 0.00),
(96, 16, 75, 1, NULL, '', NULL, '', 0.00),
(97, 16, 130, 1, NULL, '', NULL, '', 0.00),
(98, 16, 32, 1, NULL, '', NULL, '', 0.00),
(99, 16, 75, 1, NULL, '', NULL, '', 0.00),
(100, 16, 61, 1, NULL, '', NULL, '', 0.00),
(101, 16, 75, 1, NULL, '', NULL, '', 0.00),
(102, 16, 219, 1, NULL, '', NULL, '', 0.00),
(103, 16, 23, 1, NULL, '', NULL, '', 0.00),
(104, 16, 116, 1, NULL, '', NULL, '', 0.00),
(105, 16, 130, 1, NULL, '', NULL, '', 0.00),
(106, 16, 25, 4, NULL, '', NULL, '', 0.00),
(107, 16, 219, 4, NULL, '', NULL, '', 0.00),
(108, 16, 77, 1, NULL, '', NULL, '', 0.00),
(109, 16, 113, 1, NULL, '', NULL, '', 0.00),
(110, 16, 219, 1, NULL, '', NULL, '', 0.00),
(111, 16, 23, 1, NULL, '', NULL, '', 0.00),
(112, 16, 130, 1, NULL, '', NULL, '', 0.00),
(113, 16, 219, 1, NULL, '', NULL, '', 0.00),
(114, 16, 192, 1, NULL, '', NULL, '', 0.00),
(115, 16, 75, 1, NULL, '', NULL, '', 0.00),
(116, 16, 120, 1, NULL, '', NULL, '', 0.00),
(117, 16, 70, 2, NULL, '', NULL, '', 0.00),
(118, 16, 69, 2, NULL, '', NULL, '', 0.00),
(119, 16, 102, 2, NULL, '', NULL, '', 0.00),
(120, 16, 106, 2, NULL, '', NULL, '', 0.00),
(121, 17, 28, 2, NULL, '', NULL, '', 0.00),
(122, 17, 9, 5, NULL, '', NULL, '', 6.00),
(123, 17, 8, 2, NULL, '', NULL, 'besar', 0.00),
(124, 17, 75, 100, NULL, '', NULL, '', 0.00),
(125, 17, 192, 2, 'no_special', NULL, 'nila', 'kecil', 0.00);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `daily_menu_stock`
--
ALTER TABLE `daily_menu_stock`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `menu_id` (`menu_id`,`stock_date`);

--
-- Indexes for table `fish_size_prices`
--
ALTER TABLE `fish_size_prices`
  ADD PRIMARY KEY (`size_category`);

--
-- Indexes for table `fish_stock`
--
ALTER TABLE `fish_stock`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fish_type_id` (`fish_type_id`);

--
-- Indexes for table `fish_types`
--
ALTER TABLE `fish_types`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `menus`
--
ALTER TABLE `menus`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `reservations`
--
ALTER TABLE `reservations`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `reservation_items`
--
ALTER TABLE `reservation_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `reservation_id` (`reservation_id`),
  ADD KEY `menu_id` (`menu_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `daily_menu_stock`
--
ALTER TABLE `daily_menu_stock`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7690;

--
-- AUTO_INCREMENT for table `fish_stock`
--
ALTER TABLE `fish_stock`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=68;

--
-- AUTO_INCREMENT for table `fish_types`
--
ALTER TABLE `fish_types`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `menus`
--
ALTER TABLE `menus`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=249;

--
-- AUTO_INCREMENT for table `reservations`
--
ALTER TABLE `reservations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `reservation_items`
--
ALTER TABLE `reservation_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=126;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `daily_menu_stock`
--
ALTER TABLE `daily_menu_stock`
  ADD CONSTRAINT `daily_menu_stock_ibfk_1` FOREIGN KEY (`menu_id`) REFERENCES `menus` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `fish_stock`
--
ALTER TABLE `fish_stock`
  ADD CONSTRAINT `fish_stock_ibfk_1` FOREIGN KEY (`fish_type_id`) REFERENCES `fish_types` (`id`);

--
-- Constraints for table `reservation_items`
--
ALTER TABLE `reservation_items`
  ADD CONSTRAINT `reservation_items_ibfk_1` FOREIGN KEY (`reservation_id`) REFERENCES `reservations` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `reservation_items_ibfk_2` FOREIGN KEY (`menu_id`) REFERENCES `menus` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
