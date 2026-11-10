-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: db:3306
-- Generation Time: Nov 10, 2026 at 09:27 PM
-- Server version: 8.4.13
-- PHP Version: 8.3.26

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `panaderia`
--

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 3, 'add_permission'),
(6, 'Can change permission', 3, 'change_permission'),
(7, 'Can delete permission', 3, 'delete_permission'),
(8, 'Can view permission', 3, 'view_permission'),
(9, 'Can add group', 2, 'add_group'),
(10, 'Can change group', 2, 'change_group'),
(11, 'Can delete group', 2, 'delete_group'),
(12, 'Can view group', 2, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add categoria', 7, 'add_categoria'),
(26, 'Can change categoria', 7, 'change_categoria'),
(27, 'Can delete categoria', 7, 'delete_categoria'),
(28, 'Can view categoria', 7, 'view_categoria'),
(29, 'Can add cliente', 8, 'add_cliente'),
(30, 'Can change cliente', 8, 'change_cliente'),
(31, 'Can delete cliente', 8, 'delete_cliente'),
(32, 'Can view cliente', 8, 'view_cliente'),
(33, 'Can add rol', 13, 'add_rol'),
(34, 'Can change rol', 13, 'change_rol'),
(35, 'Can delete rol', 13, 'delete_rol'),
(36, 'Can view rol', 13, 'view_rol'),
(37, 'Can add producto', 12, 'add_producto'),
(38, 'Can change producto', 12, 'change_producto'),
(39, 'Can delete producto', 12, 'delete_producto'),
(40, 'Can view producto', 12, 'view_producto'),
(41, 'Can add usuario', 14, 'add_usuario'),
(42, 'Can change usuario', 14, 'change_usuario'),
(43, 'Can delete usuario', 14, 'delete_usuario'),
(44, 'Can view usuario', 14, 'view_usuario'),
(45, 'Can add encargo', 11, 'add_encargo'),
(46, 'Can change encargo', 11, 'change_encargo'),
(47, 'Can delete encargo', 11, 'delete_encargo'),
(48, 'Can view encargo', 11, 'view_encargo'),
(49, 'Can add venta', 15, 'add_venta'),
(50, 'Can change venta', 15, 'change_venta'),
(51, 'Can delete venta', 15, 'delete_venta'),
(52, 'Can view venta', 15, 'view_venta'),
(53, 'Can add detalle venta', 10, 'add_detalleventa'),
(54, 'Can change detalle venta', 10, 'change_detalleventa'),
(55, 'Can delete detalle venta', 10, 'delete_detalleventa'),
(56, 'Can view detalle venta', 10, 'view_detalleventa'),
(57, 'Can add detalle encargo', 9, 'add_detalleencargo'),
(58, 'Can change detalle encargo', 9, 'change_detalleencargo'),
(59, 'Can delete detalle encargo', 9, 'delete_detalleencargo'),
(60, 'Can view detalle encargo', 9, 'view_detalleencargo'),
(61, 'Can add permiso', 16, 'add_permiso'),
(62, 'Can change permiso', 16, 'change_permiso'),
(63, 'Can delete permiso', 16, 'delete_permiso'),
(64, 'Can view permiso', 16, 'view_permiso'),
(65, 'Can add rol permiso', 17, 'add_rolpermiso'),
(66, 'Can change rol permiso', 17, 'change_rolpermiso'),
(67, 'Can delete rol permiso', 17, 'delete_rolpermiso'),
(68, 'Can view rol permiso', 17, 'view_rolpermiso'),
(69, 'Can add log auditoria', 18, 'add_logauditoria'),
(70, 'Can change log auditoria', 18, 'change_logauditoria'),
(71, 'Can delete log auditoria', 18, 'delete_logauditoria'),
(72, 'Can view log auditoria', 18, 'view_logauditoria');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user`
--

CREATE TABLE `auth_user` (
  `id` int NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `auth_user`
--

INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES
(1, 'pbkdf2_sha256$1500000$8xMulYaOTsE8msaDHIKCcK$nQF1G33h129XtETf/QxRVNVrgXvMgJk2jGtefr7NOH8=', '2026-09-18 21:14:33.332144', 1, 'maximilianobarro', '', '', 'maximilianobarro18@gmail.com', 1, 1, '2026-09-18 21:11:14.536049');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_groups`
--

CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_user_permissions`
--

CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `categoria`
--

CREATE TABLE `categoria` (
  `id_categoria` int NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(150) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `categoria`
--

INSERT INTO `categoria` (`id_categoria`, `nombre`, `descripcion`, `activo`) VALUES
(1, 'Facturas', 'bolleria dulce', 1),
(2, 'Panes Blancos', 'Pan hechos con harina normal', 1),
(3, 'Panes saborizados', NULL, 1),
(4, 'Galletas', 'dulces y saladas', 1),
(5, 'Pan de sandwich', 'Panes para variedad de sandwiches.', 1),
(6, 'Tortillas', NULL, 1);

-- --------------------------------------------------------

--
-- Table structure for table `cliente`
--

CREATE TABLE `cliente` (
  `id_cliente` int NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `apellido` varchar(50) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `calle` varchar(80) DEFAULT NULL,
  `numero` varchar(10) DEFAULT NULL,
  `ciudad` varchar(50) DEFAULT NULL,
  `fecha_alta` date DEFAULT NULL,
  `activo` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `cliente`
--

INSERT INTO `cliente` (`id_cliente`, `nombre`, `apellido`, `email`, `calle`, `numero`, `ciudad`, `fecha_alta`, `activo`) VALUES
(4, 'Juan Carlos', 'Bolson', 'juanbolson@gmail.com', 'Talavella', '2500', 'Salta', NULL, 0),
(5, 'Consumidor ', 'Final', '', '', '', '', NULL, 1),
(6, 'Juan Carlos', 'Bolsom', 'juanbolson@gmail.com', 'Rio del Valle', '2546', 'Salta', NULL, 1),
(7, 'Juan Carlos', 'Bolso', 'juanbolson@gmail.com', 'Rio del Valle', '2546', 'Salta', NULL, 1);

-- --------------------------------------------------------

--
-- Table structure for table `detalle_encargo`
--

CREATE TABLE `detalle_encargo` (
  `id` bigint NOT NULL,
  `cantidad` int NOT NULL,
  `precio_unitario` decimal(10,2) DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT NULL,
  `producto_id_producto` int NOT NULL,
  `encargo_id_encargo` int NOT NULL,
  `preparado` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `detalle_encargo`
--

INSERT INTO `detalle_encargo` (`id`, `cantidad`, `precio_unitario`, `subtotal`, `producto_id_producto`, `encargo_id_encargo`, `preparado`) VALUES
(1, 10, 1500.00, 15000.00, 8, 2, 0),
(2, 20, 100.00, 2000.00, 9, 3, 0);

-- --------------------------------------------------------

--
-- Table structure for table `detalle_venta`
--

CREATE TABLE `detalle_venta` (
  `id` bigint NOT NULL,
  `cantidad` int NOT NULL,
  `precio_unitario_venta` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `venta_id_venta` int NOT NULL,
  `producto_id_producto` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `detalle_venta`
--

INSERT INTO `detalle_venta` (`id`, `cantidad`, `precio_unitario_venta`, `subtotal`, `venta_id_venta`, `producto_id_producto`) VALUES
(1, 7, 1500.00, 10500.00, 1, 1),
(2, 3, 1500.00, 4500.00, 2, 1),
(3, 20, 1500.00, 30000.00, 3, 1),
(4, 300, 1500.00, 450000.00, 4, 1),
(5, 5, 1500.00, 7500.00, 5, 1),
(6, 3, 700.00, 2100.00, 5, 3),
(7, 3, 200.00, 600.00, 6, 4),
(8, 1, 1500.00, 1500.00, 7, 1),
(9, 3, 700.00, 2100.00, 7, 3),
(10, 3, 200.00, 600.00, 7, 4),
(11, 12, 1500.00, 18000.00, 8, 1),
(12, 2, 700.00, 1400.00, 8, 3),
(13, 5, 200.00, 1000.00, 8, 4),
(14, 289, 200.00, 57800.00, 9, 4),
(15, 1, 1500.00, 1500.00, 10, 1),
(16, 1, 700.00, 700.00, 10, 3),
(17, 10, 1500.00, 15000.00, 11, 1),
(18, 1, 700.00, 700.00, 11, 3),
(19, 3, 200.00, 600.00, 12, 4),
(20, 2, 700.00, 1400.00, 13, 3),
(21, 3, 1000.00, 3000.00, 14, 7),
(22, 3, 1500.00, 4500.00, 14, 8);

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint UNSIGNED NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(2, 'auth', 'group'),
(3, 'auth', 'permission'),
(4, 'auth', 'user'),
(5, 'contenttypes', 'contenttype'),
(7, 'core', 'categoria'),
(8, 'core', 'cliente'),
(9, 'core', 'detalleencargo'),
(10, 'core', 'detalleventa'),
(11, 'core', 'encargo'),
(18, 'core', 'logauditoria'),
(16, 'core', 'permiso'),
(12, 'core', 'producto'),
(13, 'core', 'rol'),
(17, 'core', 'rolpermiso'),
(14, 'core', 'usuario'),
(15, 'core', 'venta'),
(6, 'sessions', 'session');

-- --------------------------------------------------------

--
-- Table structure for table `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(18, 'core', '0001_initial', '2026-09-17 23:25:17.234508'),
(19, 'core', '0002_alter_cliente_fecha_alta_alter_producto_categoria_and_more', '2026-09-17 23:25:17.245860'),
(20, 'core', '0003_detalleventa_id_alter_detalleventa_producto_and_more', '2026-09-17 23:25:17.258995'),
(22, 'contenttypes', '0001_initial', '2026-09-18 21:05:35.661642'),
(23, 'auth', '0001_initial', '2026-09-18 21:05:36.929658'),
(24, 'admin', '0001_initial', '2026-09-18 21:05:37.208452'),
(25, 'admin', '0002_logentry_remove_auto_add', '2026-09-18 21:05:37.220297'),
(26, 'admin', '0003_logentry_add_action_flag_choices', '2026-09-18 21:05:37.231657'),
(27, 'contenttypes', '0002_remove_content_type_name', '2026-09-18 21:05:37.456953'),
(28, 'auth', '0002_alter_permission_name_max_length', '2026-09-18 21:05:37.573737'),
(29, 'auth', '0003_alter_user_email_max_length', '2026-09-18 21:05:37.604658'),
(30, 'auth', '0004_alter_user_username_opts', '2026-09-18 21:05:37.615412'),
(31, 'auth', '0005_alter_user_last_login_null', '2026-09-18 21:05:37.716107'),
(32, 'auth', '0006_require_contenttypes_0002', '2026-09-18 21:05:37.722733'),
(33, 'auth', '0007_alter_validators_add_error_messages', '2026-09-18 21:05:37.733522'),
(34, 'auth', '0008_alter_user_username_max_length', '2026-09-18 21:05:37.853389'),
(35, 'auth', '0009_alter_user_last_name_max_length', '2026-09-18 21:05:37.970275'),
(36, 'auth', '0010_alter_group_name_max_length', '2026-09-18 21:05:38.008388'),
(37, 'auth', '0011_update_proxy_permissions', '2026-09-18 21:05:38.027057'),
(38, 'auth', '0012_alter_user_first_name_max_length', '2026-09-18 21:05:38.152474'),
(39, 'sessions', '0001_initial', '2026-09-18 21:05:38.230185'),
(40, 'core', '0004_permiso_usuario_activo_usuario_debe_cambiar_clave_and_more', '2026-09-24 01:12:44.898680'),
(41, 'core', '0005_rol_permisos', '2026-10-07 03:13:13.466470'),
(42, 'core', '0006_remove_producto_unidad_medida', '2026-10-14 23:35:49.546328'),
(43, 'core', '0007_venta_fecha_anulacion_venta_motivo_anulacion_and_more', '2026-10-20 01:35:42.419940'),
(44, 'core', '0008_cliente_activo_logauditoria', '2026-10-31 00:01:05.398554'),
(45, 'core', '0009_encargo_cantidad_items_medio_pago', '2026-11-02 22:46:53.006497'),
(46, 'core', '0010_encargo_proceso_completo', '2026-11-04 00:54:13.333754'),
(47, 'core', '0011_activo_rol_permiso_categoria', '2026-11-06 22:45:48.849189'),
(48, 'core', '0012_detalleencargo_preparado', '2026-11-09 22:57:24.116520');

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('4kudqho6bwhwg606dccpnorovim9d8n7', 'eyJ1c3VhcmlvX2lkIjoxLCJub21icmVfdXN1YXJpbyI6ImFkbWluc2lzIn0:1xCmBK:rF-VvLvnid7gjic8UnxFBx69ct1weln81AYxAZ6jUsI', '2026-10-16 22:56:46.104299'),
('inim8r7eyatbhvi14y3zbfr1klqg6ail', 'eyJ1c3VhcmlvX2lkIjoxLCJub21icmVfdXN1YXJpbyI6ImFkbWluc2lzIn0:1xQR6s:7TRzxVk9pEm_5pVmzfo6UxUYLhsHfYYmXYhlwLnNopk', '2026-11-23 15:16:38.705108'),
('klzf48vm1a78z7qylb16hlkc2kut6obg', 'eyJ1c3VhcmlvX2lkIjo5LCJub21icmVfdXN1YXJpbyI6ImJhcnJvbSJ9:1xPRPF:uua5loboTHhg9iOpm--RykYOqr5u29mfQuiL8jw-bb4', '2026-11-20 21:23:29.859840'),
('v55pdrc3oma4t5zwgczyjtjzk44lj7b4', 'eyJ1c3VhcmlvX2lkIjoxLCJub21icmVfdXN1YXJpbyI6ImFkbWluc2lzIn0:1xFb20:LbxyLKxB_tPMGJ4jsDbwoWFbvKropa0BHeHbD0BGTT8', '2026-10-24 17:38:48.277806');

-- --------------------------------------------------------

--
-- Table structure for table `encargo`
--

CREATE TABLE `encargo` (
  `id_encargo` int NOT NULL,
  `fecha_pedido` date DEFAULT NULL,
  `fecha_entrega_prevista` date DEFAULT NULL,
  `senia` decimal(10,2) DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `observacion` varchar(200) DEFAULT NULL,
  `usuario_id_usuario` int NOT NULL,
  `cliente_id_cliente` int NOT NULL,
  `medio_pago` varchar(20) DEFAULT NULL,
  `total` decimal(12,2) NOT NULL,
  `fecha_entrega_real` datetime(6) DEFAULT NULL,
  `fecha_anulacion` datetime(6) DEFAULT NULL,
  `motivo_anulacion` varchar(200) DEFAULT NULL,
  `usuario_anulacion_id_usuario` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `encargo`
--

INSERT INTO `encargo` (`id_encargo`, `fecha_pedido`, `fecha_entrega_prevista`, `senia`, `estado`, `observacion`, `usuario_id_usuario`, `cliente_id_cliente`, `medio_pago`, `total`, `fecha_entrega_real`, `fecha_anulacion`, `motivo_anulacion`, `usuario_anulacion_id_usuario`) VALUES
(1, '2026-11-02', '2026-11-03', 100000.00, NULL, 'Docena de medialunas de manteca, 200 tostadas, 15 bagettes, 20 tortillas', 9, 4, 'Efectivo', 0.00, NULL, NULL, NULL, NULL),
(2, '2026-11-09', '2026-11-12', 6000.00, 'Entregado', NULL, 1, 5, 'Efectivo', 15000.00, '2026-11-09 15:19:55.138104', NULL, NULL, NULL),
(3, '2026-11-09', '2026-11-11', 1000.00, 'Entregado', NULL, 1, 6, 'Efectivo', 2000.00, '2026-11-09 22:58:48.114996', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `log_auditoria`
--

CREATE TABLE `log_auditoria` (
  `id_log` int NOT NULL,
  `fecha_hora` datetime(6) NOT NULL,
  `entidad` varchar(50) NOT NULL,
  `id_registro` int NOT NULL,
  `accion` varchar(20) NOT NULL,
  `valores_anteriores` longtext,
  `valores_actuales` longtext,
  `usuario_id_usuario` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `log_auditoria`
--

INSERT INTO `log_auditoria` (`id_log`, `fecha_hora`, `entidad`, `id_registro`, `accion`, `valores_anteriores`, `valores_actuales`, `usuario_id_usuario`) VALUES
(1, '2026-10-31 00:31:17.261530', 'permiso', 22, 'ELIMINACION', '{\"nombre_permiso\": \"anular_venta\", \"descripcion\": \"Anular ventas y devolver el stock\"}', NULL, 1),
(2, '2026-10-31 07:35:57.667505', 'cliente', 4, 'MODIFICACION', '{\"activo\": true}', '{\"activo\": false}', 1),
(3, '2026-10-31 07:36:01.958123', 'cliente', 4, 'MODIFICACION', '{\"activo\": false}', '{\"activo\": true}', 1),
(4, '2026-11-03 00:30:05.110464', 'cliente', 7, 'MODIFICACION', '{\"activo\": true}', '{\"activo\": false}', 1),
(5, '2026-11-03 00:30:16.696308', 'cliente', 7, 'MODIFICACION', '{\"activo\": false}', '{\"activo\": true}', 1),
(6, '2026-11-03 00:30:21.904422', 'cliente', 7, 'MODIFICACION', '{\"activo\": true}', '{\"activo\": false}', 1),
(7, '2026-11-04 00:39:32.263838', 'permiso', 21, 'ELIMINACION', '{\"nombre_permiso\": \"Control de materia prima\", \"descripcion\": \"Supervisor para materia necesaria para la fabricacion del pan\"}', NULL, 1),
(8, '2026-11-04 01:12:34.235685', 'cliente', 6, 'MODIFICACION', '{\"activo\": true}', '{\"activo\": false}', 9),
(9, '2026-11-04 01:12:48.145570', 'cliente', 7, 'MODIFICACION', '{\"activo\": false}', '{\"activo\": true}', 9),
(10, '2026-11-04 01:24:35.373213', 'cliente', 6, 'MODIFICACION', '{\"activo\": false}', '{\"activo\": true}', 1),
(11, '2026-11-04 01:26:42.450599', 'producto', 4, 'MODIFICACION', '{\"stock_actual\": 289}', '{\"stock_actual\": 0}', 1),
(12, '2026-11-04 01:27:21.789380', 'producto', 1, 'MODIFICACION', '{\"stock_actual\": 1672}', '{\"stock_actual\": 1671}', 1),
(13, '2026-11-04 01:27:21.797671', 'producto', 3, 'MODIFICACION', '{\"stock_actual\": 392}', '{\"stock_actual\": 391}', 1),
(14, '2026-11-05 01:04:25.606006', 'cliente', 4, 'MODIFICACION', '{\"activo\": true}', '{\"activo\": false}', 1),
(15, '2026-11-05 01:04:31.190847', 'cliente', 7, 'MODIFICACION', '{\"activo\": true}', '{\"activo\": false}', 1),
(16, '2026-11-05 01:05:23.636859', 'producto', 4, 'MODIFICACION', '{\"stock_actual\": 0}', '{\"stock_actual\": 70}', 1),
(17, '2026-11-05 01:05:29.121087', 'producto', 4, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 1),
(18, '2026-11-05 01:12:27.763732', 'producto', 4, 'MODIFICACION', '{\"estado\": \"inactivo\"}', '{\"estado\": \"activo\"}', 1),
(19, '2026-11-05 01:20:27.786225', 'producto', 1, 'MODIFICACION', '{\"stock_actual\": 1671}', '{\"stock_actual\": 1670}', 9),
(20, '2026-11-06 07:32:44.958959', 'producto', 1, 'MODIFICACION', '{\"stock_actual\": 1670}', '{\"stock_actual\": 1660}', 1),
(21, '2026-11-06 07:32:44.971510', 'producto', 3, 'MODIFICACION', '{\"stock_actual\": 391}', '{\"stock_actual\": 390}', 1),
(22, '2026-11-06 07:33:14.193828', 'producto', 4, 'MODIFICACION', '{\"stock_actual\": 70}', '{\"stock_actual\": 67}', 1),
(23, '2026-11-06 07:47:32.492655', 'producto', 3, 'MODIFICACION', '{\"stock_actual\": 390}', '{\"stock_actual\": 388}', 1),
(24, '2026-11-06 22:46:40.114966', 'producto', 1, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 1),
(25, '2026-11-06 22:46:44.395682', 'producto', 1, 'MODIFICACION', '{\"estado\": \"inactivo\"}', '{\"estado\": \"activo\"}', 1),
(26, '2026-11-06 22:46:56.241370', 'producto', 3, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 1),
(27, '2026-11-06 22:46:58.476549', 'producto', 10, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 1),
(28, '2026-11-06 22:47:02.312398', 'producto', 3, 'MODIFICACION', '{\"estado\": \"inactivo\"}', '{\"estado\": \"activo\"}', 1),
(29, '2026-11-06 22:47:03.440137', 'producto', 10, 'MODIFICACION', '{\"estado\": \"inactivo\"}', '{\"estado\": \"activo\"}', 1),
(30, '2026-11-06 22:51:22.167207', 'producto', 1, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 1),
(31, '2026-11-06 22:51:24.403195', 'producto', 1, 'MODIFICACION', '{\"estado\": \"inactivo\"}', '{\"estado\": \"activo\"}', 1),
(32, '2026-11-06 22:51:39.302271', 'cliente', 7, 'MODIFICACION', '{\"activo\": false}', '{\"activo\": true}', 9),
(33, '2026-11-06 22:59:11.187209', 'producto', 1, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 9),
(34, '2026-11-06 22:59:13.170814', 'producto', 1, 'MODIFICACION', '{\"estado\": \"inactivo\"}', '{\"estado\": \"activo\"}', 9),
(35, '2026-11-06 23:17:37.588483', 'producto', 7, 'MODIFICACION', '{\"stock_actual\": 400}', '{\"stock_actual\": 397}', 9),
(36, '2026-11-06 23:17:37.596022', 'producto', 8, 'MODIFICACION', '{\"stock_actual\": 500}', '{\"stock_actual\": 497}', 9),
(37, '2026-11-06 23:18:44.166062', 'producto', 7, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 9),
(38, '2026-11-06 23:18:48.998817', 'producto', 7, 'MODIFICACION', '{\"estado\": \"inactivo\"}', '{\"estado\": \"activo\"}', 9),
(39, '2026-11-06 23:18:53.564178', 'producto', 1, 'MODIFICACION', '{\"estado\": \"activo\"}', '{\"estado\": \"inactivo\"}', 9),
(40, '2026-11-06 23:31:15.038413', 'cliente', 5, 'MODIFICACION', '{\"activo\": true}', '{\"activo\": false}', 1),
(41, '2026-11-07 01:26:59.817339', 'cliente', 5, 'MODIFICACION', '{\"activo\": false}', '{\"activo\": true}', 1),
(42, '2026-11-09 15:19:24.623960', 'producto', 8, 'MODIFICACION', '{\"stock_actual\": 497}', '{\"stock_actual\": 487}', 1),
(43, '2026-11-09 15:19:55.142150', 'encargo', 2, 'MODIFICACION', '{\"estado\": \"Pendiente\", \"fecha_entrega_real\": null}', '{\"estado\": \"Entregado\", \"fecha_entrega_real\": \"2026-11-09T15:19:55.138Z\"}', 1),
(44, '2026-11-09 22:32:16.331670', 'producto', 9, 'MODIFICACION', '{\"stock_actual\": 400}', '{\"stock_actual\": 380}', 1),
(45, '2026-11-09 22:58:48.121911', 'encargo', 3, 'MODIFICACION', '{\"estado\": \"Pendiente\", \"fecha_entrega_real\": null}', '{\"estado\": \"Entregado\", \"fecha_entrega_real\": \"2026-11-09T22:58:48.114Z\"}', 1);

-- --------------------------------------------------------

--
-- Table structure for table `permiso`
--

CREATE TABLE `permiso` (
  `id_permiso` int NOT NULL,
  `nombre_permiso` varchar(50) NOT NULL,
  `descripcion` varchar(150) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `permiso`
--

INSERT INTO `permiso` (`id_permiso`, `nombre_permiso`, `descripcion`, `activo`) VALUES
(1, 'Administracion', 'Encargado de un area', 1),
(10, 'ver_productos', NULL, 1),
(11, 'editar_stock', NULL, 1),
(12, 'ver_ventas', NULL, 1),
(13, 'ver_clientes', NULL, 1),
(14, 'registrar_cliente', NULL, 1),
(15, 'ver_categorias', NULL, 1),
(16, 'gestionar_roles', NULL, 1),
(17, 'registrar_venta', 'Registrar y modificar ventas y encargos', 1),
(18, 'gestionar_usuarios', 'Alta, baja y restablecimiento de usuarios', 1),
(20, 'emitir_comprobante', 'Emitir el comprobante de una venta', 1),
(23, 'ver_auditoria', 'Consultar el registro de auditoría', 1),
(24, 'cancelar_encargo', 'Cancelar encargos pendientes', 1),
(25, 'editar_producto', 'puede editar productos y su stock', 1),
(26, 'dar_baja_alta', 'Puede dar de alta y baja registros dentro del sistema.', 1);

-- --------------------------------------------------------

--
-- Table structure for table `producto`
--

CREATE TABLE `producto` (
  `id_producto` int NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `stock_actual` int DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `categoria_idcategoria` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `producto`
--

INSERT INTO `producto` (`id_producto`, `nombre`, `descripcion`, `precio_unitario`, `stock_actual`, `estado`, `categoria_idcategoria`) VALUES
(1, 'Medialunas de manteca', 'pan en forma de croissant dulce', 1500.00, 1660, 'inactivo', 1),
(3, 'Baguette', 'Pan largo de estilo frances', 700.00, 388, 'activo', 2),
(4, 'Chipa', 'Pan con queso', 200.00, 67, 'activo', 3),
(6, 'Tira de pan', 'tira larga de pan comun', 700.00, 2000, 'activo', 2),
(7, 'Pan para pancho', NULL, 1000.00, 397, 'activo', 5),
(8, 'Pan de hamburguesa', NULL, 1500.00, 487, 'activo', 5),
(9, 'Chatas', NULL, 100.00, 380, 'activo', 6),
(10, 'Galletas de Maicenas', NULL, 300.00, 600, 'activo', 4);

-- --------------------------------------------------------

--
-- Table structure for table `rol`
--

CREATE TABLE `rol` (
  `id_rol` int NOT NULL,
  `nombre_rol` varchar(50) NOT NULL,
  `descripcion` varchar(150) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `rol`
--

INSERT INTO `rol` (`id_rol`, `nombre_rol`, `descripcion`, `activo`) VALUES
(1, 'Administrador', 'Acceso total al sistema', 1),
(2, 'Empleado', 'Vendedor en el mostrador', 1),
(3, 'Maestro Panadero', 'Elaboración de panificados, control de stock de materia prima e insumos, gestión de producción', 1);

-- --------------------------------------------------------

--
-- Table structure for table `rol_permiso`
--

CREATE TABLE `rol_permiso` (
  `id` bigint NOT NULL,
  `permiso_id_permiso` int NOT NULL,
  `rol_id_rol` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `rol_permiso`
--

INSERT INTO `rol_permiso` (`id`, `permiso_id_permiso`, `rol_id_rol`) VALUES
(4, 1, 1),
(5, 10, 1),
(6, 11, 1),
(7, 12, 1),
(8, 13, 1),
(9, 14, 1),
(10, 15, 1),
(11, 16, 1),
(12, 17, 1),
(13, 18, 1),
(14, 10, 2),
(15, 12, 2),
(16, 13, 2),
(17, 14, 2),
(18, 17, 2),
(22, 20, 2),
(25, 25, 2),
(26, 26, 2),
(19, 10, 3),
(20, 11, 3),
(21, 15, 3),
(28, 23, 3),
(27, 26, 3);

-- --------------------------------------------------------

--
-- Table structure for table `usuario`
--

CREATE TABLE `usuario` (
  `id_usuario` int NOT NULL,
  `nombre_usuario` varchar(50) NOT NULL,
  `contrasena_hash` varchar(255) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `apellido` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `fecha_alta` date DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `rol_id_rol` int NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `debe_cambiar_clave` tinyint(1) NOT NULL,
  `dni` int NOT NULL,
  `fecha_baja` date DEFAULT NULL,
  `fecha_ultima_modificacion` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `usuario`
--

INSERT INTO `usuario` (`id_usuario`, `nombre_usuario`, `contrasena_hash`, `nombre`, `apellido`, `email`, `fecha_alta`, `estado`, `rol_id_rol`, `activo`, `debe_cambiar_clave`, `dni`, `fecha_baja`, `fecha_ultima_modificacion`) VALUES
(1, 'adminsis', 'pbkdf2_sha256$1500000$AdESkyxNW4sEL0Qcd8QRDb$I05UvOBptI0Ibj5F0OoZacC8CYEsk6LrZkvBZ0NXYsU=', 'Sistema', 'Admin', 'admin@panaderia.com', '2026-09-25', NULL, 1, 1, 0, 11111111, NULL, '2026-10-09'),
(2, 'martinezp', 'pbkdf2_sha256$1500000$FlPEUnqVoKMFb6jJSw0fZB$K/lA/2LNyk8mP+wt3vZpk36gFUvVLsPqJ9FTcBphHgU=', 'Pablo', 'Martinez', 'pablo20@gmail.com', '2026-10-09', NULL, 2, 1, 0, 39390820, NULL, '2026-10-09'),
(3, 'perezj', 'pbkdf2_sha256$1500000$Zptv6ZCPmYZou65nIsgECI$2ubFGi0AU8hVpe/RXdQ/FcumN5nBYb+XY9qErFnk0fI=', 'Juan', 'Perez', 'juanperez@gmail.com', '2026-10-09', NULL, 2, 0, 1, 2333969, '2026-10-14', '2026-10-16'),
(4, 'bragar', 'pbkdf2_sha256$1500000$E3bm4L7nGmnoOIQyAzf7WZ$HSM98d2YOWW1H2BeKk7SfEGdW8TgD6lSJig/i2Hnchk=', 'Roberto Carlos', 'Braga', 'roberto2012@gmail.com', '2026-10-13', NULL, 3, 1, 0, 37399399, NULL, '2026-10-13'),
(5, 'asdasda', 'pbkdf2_sha256$1500000$KUNCkOpyimJEBPL1V3kMrG$0BLZLgCRwRzk0ltCQaTZuUCOxvFEOAXIut14GADOjPQ=', 'asdasdas', 'asdasd', 'asdasd@gmail.com', '2026-10-13', NULL, 2, 0, 0, 40000000, '2026-10-16', '2026-10-16'),
(6, 'giovanag', 'pbkdf2_sha256$1500000$yVlaHuDSNEknFErOMOhps4$L6SomaAfRasa4ovn1Dvi5m9muVtJnDLmm4V3iKEfVbk=', 'Giorno', 'Giovana', 'giorno@gmail.com', '2026-10-14', NULL, 2, 1, 0, 39398823, NULL, '2026-10-14'),
(7, 'ramirezj', 'pbkdf2_sha256$1500000$03Y6YqRU5cd5nD2yIxvqAk$1OZJkQpBY8eh3nhcx43Kq6302lSTU8etSavLZJcfgR8=', 'Jorge', 'Ramirez', 'Jorge@gmail.com', '2026-10-14', NULL, 2, 1, 0, 40100101, NULL, '2026-10-14'),
(8, 'salazarm', 'pbkdf2_sha256$1500000$vJyZYLafIllgc9DweO8BIY$TK0E2QzgX3b1/MjNWzy/YDLNTZo7J3yC2InOpNZPbKg=', 'Marcos', 'Salazar', 'marco@gmail.com', '2026-10-16', NULL, 2, 1, 0, 39398827, NULL, '2026-10-16'),
(9, 'barrom', 'pbkdf2_sha256$1500000$VgIMU2zDLTAaIvXhfAetiy$lfiIp95LKrilug8M0GbzAymlIxFwUVGMZF5g14FYwRY=', 'Maximiliano', 'Barro', 'maximilianobarro@gmail.com', '2026-10-16', NULL, 2, 1, 0, 39398825, NULL, '2026-10-16'),
(10, 'barrol', 'pbkdf2_sha256$1500000$zhxdj1jx811ypz3jsasCgq$Z/ihc1GZUPd75yU37C63gusI8fb+DhE3rXuF+gKXnDs=', 'Lucas', 'Barro', 'lucasdiodo@gmail.com', '2026-10-16', NULL, 3, 1, 1, 39398829, NULL, '2026-10-16'),
(11, 'salazars', 'pbkdf2_sha256$1500000$uoyxmIdyrVEc1MVAcyfbPU$gDO8wlL8wXRNrbwBKZ0X3uzgaHZi920ce/eAUEFcGvc=', 'Sebastian', 'Salazar', 'Sebastian@gmail.com', '2026-10-16', NULL, 2, 1, 1, 40399399, NULL, '2026-10-16');

-- --------------------------------------------------------

--
-- Table structure for table `venta`
--

CREATE TABLE `venta` (
  `id_venta` int NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `medio_pago` varchar(30) DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `usuario_id_usuario` int NOT NULL,
  `cliente_id_cliente` int NOT NULL,
  `fecha_anulacion` datetime(6) DEFAULT NULL,
  `motivo_anulacion` varchar(200) DEFAULT NULL,
  `total` decimal(12,2) NOT NULL,
  `usuario_anulacion_id_usuario` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Dumping data for table `venta`
--

INSERT INTO `venta` (`id_venta`, `fecha_hora`, `medio_pago`, `estado`, `usuario_id_usuario`, `cliente_id_cliente`, `fecha_anulacion`, `motivo_anulacion`, `total`, `usuario_anulacion_id_usuario`) VALUES
(1, '2026-10-21 01:25:43', 'Efectivo', 'Confirmada', 1, 5, NULL, NULL, 10500.00, NULL),
(2, '2026-10-23 22:39:15', 'Transferencia', 'Confirmada', 1, 5, NULL, NULL, 4500.00, NULL),
(3, '2026-10-24 00:33:30', 'Tarjeta', 'Anulada', 1, 5, '2026-10-24 00:34:08.501336', 'CLIENTE QUERIA OTRO PRODUCTO', 30000.00, 1),
(4, '2026-10-24 00:34:45', 'Efectivo', 'Confirmada', 9, 4, NULL, NULL, 450000.00, NULL),
(5, '2026-10-24 01:03:41', 'Efectivo', 'Confirmada', 9, 5, NULL, NULL, 9600.00, NULL),
(6, '2026-10-28 01:24:19', 'Efectivo', 'Confirmada', 1, 4, NULL, NULL, 600.00, NULL),
(7, '2026-10-30 21:06:13', 'Efectivo', 'Confirmada', 1, 5, NULL, NULL, 4200.00, NULL),
(8, '2026-10-30 22:16:24', 'Transferencia', 'Confirmada', 1, 5, NULL, NULL, 20400.00, NULL),
(9, '2026-11-04 01:26:42', 'Efectivo', 'Confirmada', 1, 7, NULL, NULL, 57800.00, NULL),
(10, '2026-11-04 01:27:22', 'Efectivo', 'Confirmada', 1, 5, NULL, NULL, 2200.00, NULL),
(11, '2026-11-06 07:32:45', 'Transferencia', 'Confirmada', 1, 5, NULL, NULL, 15700.00, NULL),
(12, '2026-11-06 07:33:14', 'Tarjeta', 'Confirmada', 1, 6, NULL, NULL, 600.00, NULL),
(13, '2026-11-06 07:47:32', 'Tarjeta', 'Confirmada', 1, 5, NULL, NULL, 1400.00, NULL),
(14, '2026-11-06 23:17:38', 'Transferencia', 'Confirmada', 9, 5, NULL, NULL, 7500.00, NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Indexes for table `auth_user`
--
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);

--
-- Indexes for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  ADD KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `categoria`
--
ALTER TABLE `categoria`
  ADD PRIMARY KEY (`id_categoria`);

--
-- Indexes for table `cliente`
--
ALTER TABLE `cliente`
  ADD PRIMARY KEY (`id_cliente`);

--
-- Indexes for table `detalle_encargo`
--
ALTER TABLE `detalle_encargo`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_detalle_encargo_producto_encargo` (`producto_id_producto`,`encargo_id_encargo`),
  ADD KEY `fk_detalle_encargo_producto1_idx` (`producto_id_producto`),
  ADD KEY `fk_detalle_encargo_encargo1_idx` (`encargo_id_encargo`);

--
-- Indexes for table `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_detalle_venta_venta_producto` (`venta_id_venta`,`producto_id_producto`),
  ADD KEY `fk_detalle_venta_venta1_idx` (`venta_id_venta`),
  ADD KEY `idx_detalle_venta_producto` (`producto_id_producto`);

--
-- Indexes for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Indexes for table `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- Indexes for table `encargo`
--
ALTER TABLE `encargo`
  ADD PRIMARY KEY (`id_encargo`),
  ADD KEY `fk_encargo_usuario1_idx` (`usuario_id_usuario`),
  ADD KEY `fk_encargo_cliente1_idx` (`cliente_id_cliente`),
  ADD KEY `encargo_usuario_anulacion_id_53ac020c_fk_usuario_i` (`usuario_anulacion_id_usuario`);

--
-- Indexes for table `log_auditoria`
--
ALTER TABLE `log_auditoria`
  ADD PRIMARY KEY (`id_log`),
  ADD KEY `log_auditoria_usuario_id_usuario_d7bdecc3_fk_usuario_id_usuario` (`usuario_id_usuario`);

--
-- Indexes for table `permiso`
--
ALTER TABLE `permiso`
  ADD PRIMARY KEY (`id_permiso`);

--
-- Indexes for table `producto`
--
ALTER TABLE `producto`
  ADD PRIMARY KEY (`id_producto`),
  ADD KEY `fk_producto_categoria1_idx` (`categoria_idcategoria`);

--
-- Indexes for table `rol`
--
ALTER TABLE `rol`
  ADD PRIMARY KEY (`id_rol`);

--
-- Indexes for table `rol_permiso`
--
ALTER TABLE `rol_permiso`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `rol_permiso_rol_id_rol_permiso_id_permiso_2ba25ea2_uniq` (`rol_id_rol`,`permiso_id_permiso`),
  ADD KEY `rol_permiso_permiso_id_permiso_56a94dca_fk_permiso_id_permiso` (`permiso_id_permiso`);

--
-- Indexes for table `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `dni` (`dni`),
  ADD UNIQUE KEY `usuario_nombre_usuario_44049257_uniq` (`nombre_usuario`),
  ADD KEY `fk_usuario_rol_idx` (`rol_id_rol`);

--
-- Indexes for table `venta`
--
ALTER TABLE `venta`
  ADD PRIMARY KEY (`id_venta`),
  ADD KEY `fk_venta_usuario1_idx` (`usuario_id_usuario`),
  ADD KEY `fk_venta_cliente1_idx` (`cliente_id_cliente`),
  ADD KEY `venta_usuario_anulacion_id_70e6b0a6_fk_usuario_i` (`usuario_anulacion_id_usuario`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=73;

--
-- AUTO_INCREMENT for table `auth_user`
--
ALTER TABLE `auth_user`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `categoria`
--
ALTER TABLE `categoria`
  MODIFY `id_categoria` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `cliente`
--
ALTER TABLE `cliente`
  MODIFY `id_cliente` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `detalle_encargo`
--
ALTER TABLE `detalle_encargo`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `detalle_venta`
--
ALTER TABLE `detalle_venta`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=49;

--
-- AUTO_INCREMENT for table `encargo`
--
ALTER TABLE `encargo`
  MODIFY `id_encargo` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `log_auditoria`
--
ALTER TABLE `log_auditoria`
  MODIFY `id_log` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT for table `permiso`
--
ALTER TABLE `permiso`
  MODIFY `id_permiso` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- AUTO_INCREMENT for table `producto`
--
ALTER TABLE `producto`
  MODIFY `id_producto` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `rol`
--
ALTER TABLE `rol`
  MODIFY `id_rol` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `rol_permiso`
--
ALTER TABLE `rol_permiso`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT for table `usuario`
--
ALTER TABLE `usuario`
  MODIFY `id_usuario` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `venta`
--
ALTER TABLE `venta`
  MODIFY `id_venta` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Constraints for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Constraints for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `detalle_encargo`
--
ALTER TABLE `detalle_encargo`
  ADD CONSTRAINT `fk_detalle_encargo_encargo1` FOREIGN KEY (`encargo_id_encargo`) REFERENCES `encargo` (`id_encargo`),
  ADD CONSTRAINT `fk_detalle_encargo_producto1` FOREIGN KEY (`producto_id_producto`) REFERENCES `producto` (`id_producto`);

--
-- Constraints for table `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD CONSTRAINT `fk_detalle_venta_producto1` FOREIGN KEY (`producto_id_producto`) REFERENCES `producto` (`id_producto`),
  ADD CONSTRAINT `fk_detalle_venta_venta1` FOREIGN KEY (`venta_id_venta`) REFERENCES `venta` (`id_venta`);

--
-- Constraints for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `encargo`
--
ALTER TABLE `encargo`
  ADD CONSTRAINT `encargo_usuario_anulacion_id_53ac020c_fk_usuario_i` FOREIGN KEY (`usuario_anulacion_id_usuario`) REFERENCES `usuario` (`id_usuario`),
  ADD CONSTRAINT `fk_encargo_cliente1` FOREIGN KEY (`cliente_id_cliente`) REFERENCES `cliente` (`id_cliente`),
  ADD CONSTRAINT `fk_encargo_usuario1` FOREIGN KEY (`usuario_id_usuario`) REFERENCES `usuario` (`id_usuario`);

--
-- Constraints for table `log_auditoria`
--
ALTER TABLE `log_auditoria`
  ADD CONSTRAINT `log_auditoria_usuario_id_usuario_d7bdecc3_fk_usuario_id_usuario` FOREIGN KEY (`usuario_id_usuario`) REFERENCES `usuario` (`id_usuario`);

--
-- Constraints for table `producto`
--
ALTER TABLE `producto`
  ADD CONSTRAINT `fk_producto_categoria1` FOREIGN KEY (`categoria_idcategoria`) REFERENCES `categoria` (`id_categoria`);

--
-- Constraints for table `rol_permiso`
--
ALTER TABLE `rol_permiso`
  ADD CONSTRAINT `rol_permiso_permiso_id_permiso_56a94dca_fk_permiso_id_permiso` FOREIGN KEY (`permiso_id_permiso`) REFERENCES `permiso` (`id_permiso`),
  ADD CONSTRAINT `rol_permiso_rol_id_rol_32e9a02c_fk_rol_id_rol` FOREIGN KEY (`rol_id_rol`) REFERENCES `rol` (`id_rol`);

--
-- Constraints for table `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `fk_usuario_rol` FOREIGN KEY (`rol_id_rol`) REFERENCES `rol` (`id_rol`);

--
-- Constraints for table `venta`
--
ALTER TABLE `venta`
  ADD CONSTRAINT `fk_venta_cliente1` FOREIGN KEY (`cliente_id_cliente`) REFERENCES `cliente` (`id_cliente`),
  ADD CONSTRAINT `fk_venta_usuario1` FOREIGN KEY (`usuario_id_usuario`) REFERENCES `usuario` (`id_usuario`),
  ADD CONSTRAINT `venta_usuario_anulacion_id_70e6b0a6_fk_usuario_i` FOREIGN KEY (`usuario_anulacion_id_usuario`) REFERENCES `usuario` (`id_usuario`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
