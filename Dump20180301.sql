-- MySQL dump 10.13  Distrib 5.7.12, for Win64 (x86_64)
--
-- Host: localhost    Database: ipay4_free
-- ------------------------------------------------------
-- Server version	5.7.14-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `addr_orders`
--

DROP TABLE IF EXISTS `addr_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `addr_orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `xcurr_id` int(11) DEFAULT NULL,
  `addr` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `xcurr_id__idx` (`xcurr_id`),
  CONSTRAINT `addr_orders_ibfk_1` FOREIGN KEY (`xcurr_id`) REFERENCES `xcurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `addr_orders`
--

LOCK TABLES `addr_orders` WRITE;
/*!40000 ALTER TABLE `addr_orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `addr_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bonus`
--

DROP TABLE IF EXISTS `bonus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bonus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ph` varchar(15) DEFAULT NULL,
  `gift_code` char(1) DEFAULT NULL,
  `taken` int(11) DEFAULT NULL,
  `payed` int(11) DEFAULT NULL,
  `on_day` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bonus`
--

LOCK TABLES `bonus` WRITE;
/*!40000 ALTER TABLE `bonus` DISABLE KEYS */;
/*!40000 ALTER TABLE `bonus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bonus_trans`
--

DROP TABLE IF EXISTS `bonus_trans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bonus_trans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_id` int(11) DEFAULT NULL,
  `vol` int(11) DEFAULT NULL,
  `on_day` date DEFAULT NULL,
  `memo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ref_id__idx` (`ref_id`),
  CONSTRAINT `bonus_trans_ibfk_1` FOREIGN KEY (`ref_id`) REFERENCES `bonus` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bonus_trans`
--

LOCK TABLES `bonus_trans` WRITE;
/*!40000 ALTER TABLE `bonus_trans` DISABLE KEYS */;
/*!40000 ALTER TABLE `bonus_trans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `buy_partners`
--

DROP TABLE IF EXISTS `buy_partners`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `buy_partners` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cod` varchar(5) DEFAULT NULL,
  `unused` char(1) DEFAULT NULL,
  `tax` decimal(4,3) DEFAULT NULL,
  `fee` decimal(5,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `buy_partners`
--

LOCK TABLES `buy_partners` WRITE;
/*!40000 ALTER TABLE `buy_partners` DISABLE KEYS */;
/*!40000 ALTER TABLE `buy_partners` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `buy_partners_xw`
--

DROP TABLE IF EXISTS `buy_partners_xw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `buy_partners_xw` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `buy_partner_id` int(11) DEFAULT NULL,
  `curr_id` int(11) DEFAULT NULL,
  `addr` varchar(40) DEFAULT NULL,
  `amo` decimal(12,8) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `buy_partner_id__idx` (`buy_partner_id`),
  KEY `curr_id__idx` (`curr_id`),
  CONSTRAINT `buy_partners_xw_ibfk_1` FOREIGN KEY (`buy_partner_id`) REFERENCES `buy_partners` (`id`) ON DELETE CASCADE,
  CONSTRAINT `buy_partners_xw_ibfk_2` FOREIGN KEY (`curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `buy_partners_xw`
--

LOCK TABLES `buy_partners_xw` WRITE;
/*!40000 ALTER TABLE `buy_partners_xw` DISABLE KEYS */;
/*!40000 ALTER TABLE `buy_partners_xw` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `buyers_credit`
--

DROP TABLE IF EXISTS `buyers_credit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `buyers_credit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `acc` varchar(50) DEFAULT NULL,
  `credit` decimal(10,2) DEFAULT NULL,
  `accepted` decimal(10,2) DEFAULT NULL,
  `un_rewrite` char(1) DEFAULT NULL,
  `mess` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `buyers_credit`
--

LOCK TABLES `buyers_credit` WRITE;
/*!40000 ALTER TABLE `buyers_credit` DISABLE KEYS */;
/*!40000 ALTER TABLE `buyers_credit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `buys`
--

DROP TABLE IF EXISTS `buys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `buys` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dealer_acc_id` int(11) DEFAULT NULL,
  `buyer` varchar(50) DEFAULT NULL,
  `operation_id` varchar(50) DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `xcurr_id` int(11) DEFAULT NULL,
  `addr` varchar(60) DEFAULT NULL,
  `status` varchar(15) DEFAULT NULL,
  `status_mess` varchar(150) DEFAULT NULL,
  `txid` varchar(80) DEFAULT NULL,
  `vout` int(11) DEFAULT NULL,
  `tax_mess` longtext,
  `amo_out` decimal(16,8) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dealer_acc_id__idx` (`dealer_acc_id`),
  KEY `xcurr_id__idx` (`xcurr_id`),
  CONSTRAINT `buys_ibfk_1` FOREIGN KEY (`dealer_acc_id`) REFERENCES `dealers_accs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `buys_ibfk_2` FOREIGN KEY (`xcurr_id`) REFERENCES `xcurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `buys`
--

LOCK TABLES `buys` WRITE;
/*!40000 ALTER TABLE `buys` DISABLE KEYS */;
/*!40000 ALTER TABLE `buys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `buys_stack`
--

DROP TABLE IF EXISTS `buys_stack`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `buys_stack` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_` int(11) DEFAULT NULL,
  `in_proc` char(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ref___idx` (`ref_`),
  CONSTRAINT `buys_stack_ibfk_1` FOREIGN KEY (`ref_`) REFERENCES `buys` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `buys_stack`
--

LOCK TABLES `buys_stack` WRITE;
/*!40000 ALTER TABLE `buys_stack` DISABLE KEYS */;
/*!40000 ALTER TABLE `buys_stack` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deal_id` int(11) DEFAULT NULL,
  `email` varchar(60) DEFAULT NULL,
  `auto_collect` char(1) DEFAULT NULL,
  `note_url` longtext,
  `auto_convert` char(1) DEFAULT NULL,
  `conv_curr_id` int(11) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `deal_id` (`deal_id`),
  UNIQUE KEY `email` (`email`),
  KEY `deal_id__idx` (`deal_id`),
  KEY `conv_curr_id__idx` (`conv_curr_id`),
  CONSTRAINT `clients_ibfk_1` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE CASCADE,
  CONSTRAINT `clients_ibfk_2` FOREIGN KEY (`conv_curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients`
--

LOCK TABLES `clients` WRITE;
/*!40000 ALTER TABLE `clients` DISABLE KEYS */;
/*!40000 ALTER TABLE `clients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients_balances`
--

DROP TABLE IF EXISTS `clients_balances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients_balances` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `curr_id` int(11) DEFAULT NULL,
  `bal` decimal(16,8) DEFAULT NULL,
  `updated_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id__idx` (`client_id`),
  KEY `curr_id__idx` (`curr_id`),
  CONSTRAINT `clients_balances_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
  CONSTRAINT `clients_balances_ibfk_2` FOREIGN KEY (`curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients_balances`
--

LOCK TABLES `clients_balances` WRITE;
/*!40000 ALTER TABLE `clients_balances` DISABLE KEYS */;
/*!40000 ALTER TABLE `clients_balances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients_ewallets`
--

DROP TABLE IF EXISTS `clients_ewallets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients_ewallets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `dealer_id` int(11) DEFAULT NULL,
  `ecurr_id` int(11) DEFAULT NULL,
  `addr` varchar(40) DEFAULT NULL,
  `bal` decimal(16,3) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id__idx` (`client_id`),
  KEY `dealer_id__idx` (`dealer_id`),
  KEY `ecurr_id__idx` (`ecurr_id`),
  CONSTRAINT `clients_ewallets_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
  CONSTRAINT `clients_ewallets_ibfk_2` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `clients_ewallets_ibfk_3` FOREIGN KEY (`ecurr_id`) REFERENCES `ecurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients_ewallets`
--

LOCK TABLES `clients_ewallets` WRITE;
/*!40000 ALTER TABLE `clients_ewallets` DISABLE KEYS */;
/*!40000 ALTER TABLE `clients_ewallets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients_notifies`
--

DROP TABLE IF EXISTS `clients_notifies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients_notifies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `clients_tran_id` int(11) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `resp` char(1) DEFAULT NULL,
  `tries` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `clients_tran_id__idx` (`clients_tran_id`),
  CONSTRAINT `clients_notifies_ibfk_1` FOREIGN KEY (`clients_tran_id`) REFERENCES `clients_trans` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients_notifies`
--

LOCK TABLES `clients_notifies` WRITE;
/*!40000 ALTER TABLE `clients_notifies` DISABLE KEYS */;
/*!40000 ALTER TABLE `clients_notifies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients_trans`
--

DROP TABLE IF EXISTS `clients_trans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients_trans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `order_id` varchar(100) DEFAULT NULL,
  `curr_out_id` int(11) DEFAULT NULL,
  `amo_out` decimal(16,8) DEFAULT NULL,
  `curr_in_id` int(11) DEFAULT NULL,
  `amo_in` decimal(16,8) DEFAULT NULL,
  `desc_` longtext,
  `created_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id__idx` (`client_id`),
  KEY `curr_out_id__idx` (`curr_out_id`),
  KEY `curr_in_id__idx` (`curr_in_id`),
  CONSTRAINT `clients_trans_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
  CONSTRAINT `clients_trans_ibfk_2` FOREIGN KEY (`curr_out_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `clients_trans_ibfk_3` FOREIGN KEY (`curr_in_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients_trans`
--

LOCK TABLES `clients_trans` WRITE;
/*!40000 ALTER TABLE `clients_trans` DISABLE KEYS */;
/*!40000 ALTER TABLE `clients_trans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients_xwallets`
--

DROP TABLE IF EXISTS `clients_xwallets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients_xwallets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_id` int(11) DEFAULT NULL,
  `xcurr_id` int(11) DEFAULT NULL,
  `addr` varchar(40) DEFAULT NULL,
  `bal` decimal(16,8) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id__idx` (`client_id`),
  KEY `xcurr_id__idx` (`xcurr_id`),
  CONSTRAINT `clients_xwallets_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
  CONSTRAINT `clients_xwallets_ibfk_2` FOREIGN KEY (`xcurr_id`) REFERENCES `xcurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients_xwallets`
--

LOCK TABLES `clients_xwallets` WRITE;
/*!40000 ALTER TABLE `clients_xwallets` DISABLE KEYS */;
/*!40000 ALTER TABLE `clients_xwallets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `currs`
--

DROP TABLE IF EXISTS `currs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `currs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `abbrev` varchar(5) DEFAULT NULL,
  `used` char(1) DEFAULT NULL,
  `name` varchar(25) DEFAULT NULL,
  `name2` varchar(25) DEFAULT NULL,
  `icon` varchar(512) DEFAULT NULL,
  `balance` decimal(16,8) DEFAULT NULL,
  `deposit` decimal(16,8) DEFAULT NULL,
  `clients_deposit` decimal(16,8) DEFAULT NULL,
  `max_bal` decimal(16,8) DEFAULT NULL,
  `fee_in` decimal(10,8) DEFAULT NULL,
  `fee_out` decimal(10,8) DEFAULT NULL,
  `tax_in` decimal(4,2) DEFAULT NULL,
  `tax_out` decimal(4,2) DEFAULT NULL,
  `uses` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `abbrev` (`abbrev`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `name2` (`name2`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `currs`
--

LOCK TABLES `currs` WRITE;
/*!40000 ALTER TABLE `currs` DISABLE KEYS */;
INSERT INTO `currs` VALUES (1,'USD','T','US dollar','usd',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(2,'RUB','T','Ruble','ruble',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(3,'BTC','T','Bitcoin','bitcoin',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(4,'LTC','T','Litecoin','litecoin',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(5,'DOGE','T','DOGE','doge',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(6,'DASH','T','DASH','dash',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(7,'EMC','T','Emercoin','emercoin',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(8,'NVC','T','Novacoin','novacoin',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(9,'ERA','T','ERA','ERA',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0),(10,'COMPU','T','COMPU','COMPU',NULL,0.00000000,0.00000000,0.00000000,0.00000000,0.00100000,0.00100000,0.00,0.01,0);
/*!40000 ALTER TABLE `currs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `currs_stats`
--

DROP TABLE IF EXISTS `currs_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `currs_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `curr_id` int(11) DEFAULT NULL,
  `deal_id` int(11) DEFAULT NULL,
  `average_` decimal(16,8) DEFAULT NULL,
  `count_` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `curr_id__idx` (`curr_id`),
  KEY `deal_id__idx` (`deal_id`),
  CONSTRAINT `currs_stats_ibfk_1` FOREIGN KEY (`curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `currs_stats_ibfk_2` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `currs_stats`
--

LOCK TABLES `currs_stats` WRITE;
/*!40000 ALTER TABLE `currs_stats` DISABLE KEYS */;
/*!40000 ALTER TABLE `currs_stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deal_acc_addrs`
--

DROP TABLE IF EXISTS `deal_acc_addrs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deal_acc_addrs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deal_acc_id` int(11) DEFAULT NULL,
  `unused` char(1) DEFAULT NULL,
  `xcurr_id` int(11) DEFAULT NULL,
  `addr` varchar(40) DEFAULT NULL,
  `addr_return` varchar(40) DEFAULT NULL,
  `incomed` decimal(16,8) DEFAULT NULL,
  `converted` decimal(16,8) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `deal_acc_id__idx` (`deal_acc_id`),
  KEY `xcurr_id__idx` (`xcurr_id`),
  CONSTRAINT `deal_acc_addrs_ibfk_1` FOREIGN KEY (`deal_acc_id`) REFERENCES `deal_accs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `deal_acc_addrs_ibfk_2` FOREIGN KEY (`xcurr_id`) REFERENCES `xcurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deal_acc_addrs`
--

LOCK TABLES `deal_acc_addrs` WRITE;
/*!40000 ALTER TABLE `deal_acc_addrs` DISABLE KEYS */;
/*!40000 ALTER TABLE `deal_acc_addrs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deal_accs`
--

DROP TABLE IF EXISTS `deal_accs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deal_accs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deal_id` int(11) DEFAULT NULL,
  `curr_id` int(11) DEFAULT NULL,
  `acc` varchar(100) DEFAULT NULL,
  `price` decimal(16,8) DEFAULT NULL,
  `expire` int(11) DEFAULT NULL,
  `to_pay` decimal(16,8) DEFAULT NULL,
  `payed` decimal(16,8) DEFAULT NULL,
  `payed_month` decimal(16,8) DEFAULT NULL,
  `payed_month_num` int(11) DEFAULT NULL,
  `payed3` decimal(16,8) DEFAULT NULL,
  `partner` varchar(20) DEFAULT NULL,
  `partner_sum` decimal(16,8) DEFAULT NULL,
  `partner_payed` decimal(16,8) DEFAULT NULL,
  `gift` varchar(20) DEFAULT NULL,
  `gift_try` int(11) DEFAULT NULL,
  `gift_amount` decimal(16,8) DEFAULT NULL,
  `gift_pick` decimal(14,8) DEFAULT NULL,
  `gift_payed` decimal(16,8) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `deal_id__idx` (`deal_id`),
  KEY `curr_id__idx` (`curr_id`),
  CONSTRAINT `deal_accs_ibfk_1` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE CASCADE,
  CONSTRAINT `deal_accs_ibfk_2` FOREIGN KEY (`curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deal_accs`
--

LOCK TABLES `deal_accs` WRITE;
/*!40000 ALTER TABLE `deal_accs` DISABLE KEYS */;
/*!40000 ALTER TABLE `deal_accs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deal_accs_notifies`
--

DROP TABLE IF EXISTS `deal_accs_notifies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deal_accs_notifies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deal_acc_id` int(11) DEFAULT NULL,
  `client_id` int(11) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `tries` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `deal_acc_id__idx` (`deal_acc_id`),
  KEY `client_id__idx` (`client_id`),
  CONSTRAINT `deal_accs_notifies_ibfk_1` FOREIGN KEY (`deal_acc_id`) REFERENCES `deal_accs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `deal_accs_notifies_ibfk_2` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deal_accs_notifies`
--

LOCK TABLES `deal_accs_notifies` WRITE;
/*!40000 ALTER TABLE `deal_accs_notifies` DISABLE KEYS */;
/*!40000 ALTER TABLE `deal_accs_notifies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deal_errs`
--

DROP TABLE IF EXISTS `deal_errs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deal_errs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deal_id` int(11) DEFAULT NULL,
  `dealer_id` int(11) DEFAULT NULL,
  `dealer_acc` varchar(50) DEFAULT NULL,
  `acc` varchar(50) DEFAULT NULL,
  `count_` int(11) DEFAULT NULL,
  `err` longtext,
  `updated_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `deal_id__idx` (`deal_id`),
  KEY `dealer_id__idx` (`dealer_id`),
  CONSTRAINT `deal_errs_ibfk_1` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE CASCADE,
  CONSTRAINT `deal_errs_ibfk_2` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deal_errs`
--

LOCK TABLES `deal_errs` WRITE;
/*!40000 ALTER TABLE `deal_errs` DISABLE KEYS */;
/*!40000 ALTER TABLE `deal_errs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dealer_deal_errs`
--

DROP TABLE IF EXISTS `dealer_deal_errs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dealer_deal_errs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dealer_deal_id` int(11) DEFAULT NULL,
  `acc` varchar(50) DEFAULT NULL,
  `mess` longtext,
  PRIMARY KEY (`id`),
  KEY `dealer_deal_id__idx` (`dealer_deal_id`),
  CONSTRAINT `dealer_deal_errs_ibfk_1` FOREIGN KEY (`dealer_deal_id`) REFERENCES `dealer_deals` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dealer_deal_errs`
--

LOCK TABLES `dealer_deal_errs` WRITE;
/*!40000 ALTER TABLE `dealer_deal_errs` DISABLE KEYS */;
/*!40000 ALTER TABLE `dealer_deal_errs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dealer_deals`
--

DROP TABLE IF EXISTS `dealer_deals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dealer_deals` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dealer_id` int(11) DEFAULT NULL,
  `deal_id` int(11) DEFAULT NULL,
  `used` char(1) DEFAULT NULL,
  `scid` varchar(50) DEFAULT NULL,
  `taken` int(11) DEFAULT NULL,
  `wanted` int(11) DEFAULT NULL,
  `template_` longtext,
  `calcs_` longtext,
  `grab_form` char(1) DEFAULT NULL,
  `p2p` char(1) DEFAULT NULL,
  `fee` decimal(6,2) DEFAULT NULL,
  `tax` decimal(4,2) DEFAULT NULL,
  `fee_min` decimal(8,2) DEFAULT NULL,
  `fee_max` decimal(8,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dealer_id__idx` (`dealer_id`),
  KEY `deal_id__idx` (`deal_id`),
  CONSTRAINT `dealer_deals_ibfk_1` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `dealer_deals_ibfk_2` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dealer_deals`
--

LOCK TABLES `dealer_deals` WRITE;
/*!40000 ALTER TABLE `dealer_deals` DISABLE KEYS */;
INSERT INTO `dealer_deals` VALUES (1,1,4,'F','phone-topup',0,0,NULL,NULL,'F','F',0.00,0.00,0.00,0.00),(2,1,3,'F','p2p',0,0,'[\"not_mod\", { \"n\": \"p2p\"}]',NULL,'F','T',0.00,0.50,0.00,0.00);
/*!40000 ALTER TABLE `dealer_deals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dealers`
--

DROP TABLE IF EXISTS `dealers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dealers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `used` char(1) DEFAULT NULL,
  `balance` decimal(12,2) DEFAULT NULL,
  `deposit` decimal(16,3) DEFAULT NULL,
  `clients_deposit` decimal(16,3) DEFAULT NULL,
  `API` longtext,
  `info` longtext,
  `pay_out_MIN` decimal(6,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dealers`
--

LOCK TABLES `dealers` WRITE;
/*!40000 ALTER TABLE `dealers` DISABLE KEYS */;
INSERT INTO `dealers` VALUES (1,'Yandex','T',0.00,0.000,0.000,'{ \"URI_YM_API\": \"https://money.yandex.ru/api\", \"URI_YM_AUTH\": \"https://sp-money.yandex.ru/oauth/authorize\", \"URI_YM_TOKEN\": \"https://sp-money.yandex.ru/oauth/token\", \"acc_names\": [\"user\", \"PROPERTY1\", \"rapida_param1\", \"customerNumber\", \"CustomerNumber\"] }','{ \"shops_url\": \"https://money.yandex.ru/shop.xml?scid=\", \"search_url\": \"https://money.yandex.ru/\", \"img_url\": \"https://money.yandex.ru\" }',10.00);
/*!40000 ALTER TABLE `dealers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dealers_accs`
--

DROP TABLE IF EXISTS `dealers_accs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dealers_accs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dealer_id` int(11) DEFAULT NULL,
  `ecurr_id` int(11) DEFAULT NULL,
  `used` char(1) DEFAULT NULL,
  `acc` varchar(50) DEFAULT NULL,
  `pkey` longtext,
  `skey` longtext,
  `expired` date DEFAULT NULL,
  `info` longtext,
  `reserve_MIN` decimal(12,2) DEFAULT NULL,
  `reserve_MAX` decimal(12,2) DEFAULT NULL,
  `balance` decimal(12,2) DEFAULT NULL,
  `deposit` decimal(12,2) DEFAULT NULL,
  `limited` char(1) DEFAULT NULL,
  `day_limit` int(11) DEFAULT NULL,
  `day_limit_sum` int(11) DEFAULT NULL,
  `mon_limit` int(11) DEFAULT NULL,
  `mon_limit_sum` int(11) DEFAULT NULL,
  `from_dt` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dealer_id__idx` (`dealer_id`),
  KEY `ecurr_id__idx` (`ecurr_id`),
  CONSTRAINT `dealers_accs_ibfk_1` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `dealers_accs_ibfk_2` FOREIGN KEY (`ecurr_id`) REFERENCES `ecurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dealers_accs`
--

LOCK TABLES `dealers_accs` WRITE;
/*!40000 ALTER TABLE `dealers_accs` DISABLE KEYS */;
INSERT INTO `dealers_accs` VALUES (1,1,2,'T','4100134701234567','{\"YM_REDIRECT_URI\": \"https://7pay.in/ed_YD/yandex_response\", \"secret_response\": \"**secret response**\", \"CLIENT_ID\": \"**TOKEN**\", \"SCOPE\": \"account-info operation-history operation-details payment-shop.limit(1,37777) payment-p2p.limit(1,37777)\"}',NULL,'2216-02-10',NULL,NULL,NULL,9999999.00,0.00,'T',NULL,NULL,NULL,NULL,'0');
/*!40000 ALTER TABLE `dealers_accs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dealers_accs_trans`
--

DROP TABLE IF EXISTS `dealers_accs_trans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dealers_accs_trans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dealer_acc_id` int(11) DEFAULT NULL,
  `info` longtext,
  `vars` longtext,
  `amo` decimal(12,2) DEFAULT NULL,
  `balance` decimal(16,2) DEFAULT NULL,
  `diff` decimal(16,2) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `op_id` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dealer_acc_id__idx` (`dealer_acc_id`),
  CONSTRAINT `dealers_accs_trans_ibfk_1` FOREIGN KEY (`dealer_acc_id`) REFERENCES `dealers_accs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dealers_accs_trans`
--

LOCK TABLES `dealers_accs_trans` WRITE;
/*!40000 ALTER TABLE `dealers_accs_trans` DISABLE KEYS */;
/*!40000 ALTER TABLE `dealers_accs_trans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deals`
--

DROP TABLE IF EXISTS `deals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deals` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cat_id` int(11) DEFAULT NULL,
  `fee_curr_id` int(11) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `name2` varchar(100) DEFAULT NULL,
  `show_text` longtext,
  `wants` int(11) DEFAULT NULL,
  `used` char(1) DEFAULT NULL,
  `is_shop` char(1) DEFAULT NULL,
  `not_gifted` char(1) DEFAULT NULL,
  `url` varchar(60) DEFAULT NULL,
  `my_client` char(1) DEFAULT NULL,
  `icon` varchar(512) DEFAULT NULL,
  `img` varchar(50) DEFAULT NULL,
  `template_` longtext,
  `calcs_` longtext,
  `MIN_pay` decimal(6,2) DEFAULT NULL,
  `MAX_pay` decimal(13,2) DEFAULT NULL,
  `fee` decimal(14,8) DEFAULT NULL,
  `tax` decimal(4,2) DEFAULT NULL,
  `fee_min` decimal(14,8) DEFAULT NULL,
  `fee_max` decimal(14,8) DEFAULT NULL,
  `average_` decimal(16,8) DEFAULT NULL,
  `count_` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `cat_id__idx` (`cat_id`),
  KEY `fee_curr_id__idx` (`fee_curr_id`),
  CONSTRAINT `deals_ibfk_1` FOREIGN KEY (`cat_id`) REFERENCES `deals_cat` (`id`) ON DELETE CASCADE,
  CONSTRAINT `deals_ibfk_2` FOREIGN KEY (`fee_curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deals`
--

LOCK TABLES `deals` WRITE;
/*!40000 ALTER TABLE `deals` DISABLE KEYS */;
INSERT INTO `deals` VALUES (1,1,2,'BUY','to BUY',NULL,1,'F','F','T',NULL,'F',NULL,NULL,NULL,NULL,10.00,2777.00,3.00000000,0.20,0.00000000,0.00000000,0.00000000,0),(2,1,2,'to COIN','to COIN',NULL,1,'F','F','T',NULL,'F',NULL,NULL,NULL,NULL,10.00,2777.00,3.00000000,0.20,0.00000000,0.00000000,0.00000000,0),(3,1,2,'WALLET','to WALLET',NULL,1,'F','F','T',NULL,'F',NULL,NULL,NULL,NULL,10.00,2777.00,3.00000000,0.20,0.00000000,0.00000000,0.00000000,0),(4,2,2,'phone +7','to PHONE +7',NULL,1,'F','F','T',NULL,'F',NULL,NULL,NULL,NULL,10.00,2777.00,3.00000000,0.20,0.00000000,0.00000000,0.00000000,0);
/*!40000 ALTER TABLE `deals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deals_cat`
--

DROP TABLE IF EXISTS `deals_cat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deals_cat` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `deals_cat`
--

LOCK TABLES `deals_cat` WRITE;
/*!40000 ALTER TABLE `deals_cat` DISABLE KEYS */;
INSERT INTO `deals_cat` VALUES (3,'Games'),(2,'Internet'),(5,'Municipal services'),(1,'Other'),(4,'Social');
/*!40000 ALTER TABLE `deals_cat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ecurrs`
--

DROP TABLE IF EXISTS `ecurrs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecurrs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `curr_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `curr_id__idx` (`curr_id`),
  CONSTRAINT `ecurrs_ibfk_1` FOREIGN KEY (`curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ecurrs`
--

LOCK TABLES `ecurrs` WRITE;
/*!40000 ALTER TABLE `ecurrs` DISABLE KEYS */;
INSERT INTO `ecurrs` VALUES (1,1),(2,2);
/*!40000 ALTER TABLE `ecurrs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exchg_limits`
--

DROP TABLE IF EXISTS `exchg_limits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchg_limits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exchg_id` int(11) DEFAULT NULL,
  `curr_id` int(11) DEFAULT NULL,
  `ticker` varchar(7) DEFAULT NULL,
  `reserve` decimal(16,6) DEFAULT NULL,
  `sell` decimal(16,6) DEFAULT NULL,
  `buy` decimal(16,6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `exchg_id__idx` (`exchg_id`),
  KEY `curr_id__idx` (`curr_id`),
  CONSTRAINT `exchg_limits_ibfk_1` FOREIGN KEY (`exchg_id`) REFERENCES `exchgs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `exchg_limits_ibfk_2` FOREIGN KEY (`curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchg_limits`
--

LOCK TABLES `exchg_limits` WRITE;
/*!40000 ALTER TABLE `exchg_limits` DISABLE KEYS */;
INSERT INTO `exchg_limits` VALUES (1,1,1,'',0.000000,NULL,NULL),(2,1,2,'rur',0.000000,NULL,NULL),(3,1,3,'',0.000000,NULL,NULL),(4,1,4,'',0.000000,NULL,NULL),(5,1,5,'',0.000000,NULL,NULL),(6,1,6,'',0.000000,NULL,NULL),(7,2,1,'',0.000000,NULL,NULL),(8,2,2,'',0.000000,NULL,NULL),(9,2,3,'',0.000000,NULL,NULL),(10,2,4,'',0.000000,NULL,NULL),(11,2,5,'',0.000000,NULL,NULL),(12,2,6,'',0.000000,NULL,NULL),(13,3,5,'DOGE',0.000000,NULL,NULL);
/*!40000 ALTER TABLE `exchg_limits` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exchg_pair_bases`
--

DROP TABLE IF EXISTS `exchg_pair_bases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchg_pair_bases` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `curr1_id` int(11) DEFAULT NULL,
  `curr2_id` int(11) DEFAULT NULL,
  `hard_price` decimal(16,8) DEFAULT NULL,
  `base_vol` decimal(16,8) DEFAULT NULL,
  `base_perc` decimal(5,3) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `curr1_id__idx` (`curr1_id`),
  KEY `curr2_id__idx` (`curr2_id`),
  CONSTRAINT `exchg_pair_bases_ibfk_1` FOREIGN KEY (`curr1_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `exchg_pair_bases_ibfk_2` FOREIGN KEY (`curr2_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchg_pair_bases`
--

LOCK TABLES `exchg_pair_bases` WRITE;
/*!40000 ALTER TABLE `exchg_pair_bases` DISABLE KEYS */;
INSERT INTO `exchg_pair_bases` VALUES (1,1,2,0.00000000,100.00000000,0.100),(2,1,3,0.00000000,100.00000000,0.100),(3,1,4,0.00000000,100.00000000,0.100),(4,1,5,0.00000000,100.00000000,0.100),(5,1,6,0.00000000,100.00000000,0.100),(6,1,7,0.00000000,100.00000000,0.100),(7,1,8,0.00000000,100.00000000,0.100),(8,2,1,0.00000000,10000.00000000,0.100),(9,2,3,0.00000000,10000.00000000,0.100),(10,2,4,0.00000000,10000.00000000,0.100),(11,2,5,0.00000000,10000.00000000,0.100),(12,2,6,0.00000000,10000.00000000,0.100),(13,2,7,0.00000000,10000.00000000,0.100),(14,2,8,0.00000000,10000.00000000,0.100),(15,3,1,0.00000000,1.00000000,0.100),(16,3,2,0.00000000,1.00000000,0.100),(17,3,4,0.00000000,1.00000000,0.100),(18,3,5,0.00000000,1.00000000,0.100),(19,3,6,0.00000000,1.00000000,0.100),(20,3,7,0.00000000,1.00000000,0.100),(21,3,8,0.00000000,1.00000000,0.100),(22,4,3,0.00000000,333.00000000,0.100),(23,5,3,0.00000000,3333.00000000,0.100),(24,6,3,0.00000000,3333.00000000,0.100),(25,7,3,0.00000000,33.00000000,0.100),(26,8,3,0.00000000,333.00000000,0.100),(27,9,10,0.00100000,1.00000000,0.100);
/*!40000 ALTER TABLE `exchg_pair_bases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exchg_pairs`
--

DROP TABLE IF EXISTS `exchg_pairs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchg_pairs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exchg_id` int(11) DEFAULT NULL,
  `used` char(1) DEFAULT NULL,
  `curr1_id` int(11) DEFAULT NULL,
  `curr2_id` int(11) DEFAULT NULL,
  `ticker` varchar(12) DEFAULT NULL,
  `on_update` datetime DEFAULT NULL,
  `sp1` decimal(16,8) DEFAULT NULL,
  `sv1` decimal(16,8) DEFAULT NULL,
  `sp2` decimal(16,8) DEFAULT NULL,
  `sv2` decimal(16,8) DEFAULT NULL,
  `sp3` decimal(16,8) DEFAULT NULL,
  `sv3` decimal(16,8) DEFAULT NULL,
  `sp4` decimal(16,8) DEFAULT NULL,
  `sv4` decimal(16,8) DEFAULT NULL,
  `sp5` decimal(16,8) DEFAULT NULL,
  `sv5` decimal(16,8) DEFAULT NULL,
  `bp1` decimal(16,8) DEFAULT NULL,
  `bv1` decimal(16,8) DEFAULT NULL,
  `bp2` decimal(16,8) DEFAULT NULL,
  `bv2` decimal(16,8) DEFAULT NULL,
  `bp3` decimal(16,8) DEFAULT NULL,
  `bv3` decimal(16,8) DEFAULT NULL,
  `bp4` decimal(16,8) DEFAULT NULL,
  `bv4` decimal(16,8) DEFAULT NULL,
  `bp5` decimal(16,8) DEFAULT NULL,
  `bv5` decimal(16,8) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `exchg_id__idx` (`exchg_id`),
  KEY `curr1_id__idx` (`curr1_id`),
  KEY `curr2_id__idx` (`curr2_id`),
  CONSTRAINT `exchg_pairs_ibfk_1` FOREIGN KEY (`exchg_id`) REFERENCES `exchgs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `exchg_pairs_ibfk_2` FOREIGN KEY (`curr1_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `exchg_pairs_ibfk_3` FOREIGN KEY (`curr2_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchg_pairs`
--

LOCK TABLES `exchg_pairs` WRITE;
/*!40000 ALTER TABLE `exchg_pairs` DISABLE KEYS */;
INSERT INTO `exchg_pairs` VALUES (1,1,'T',3,1,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(2,1,'T',3,2,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(3,1,'T',4,1,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(4,1,'T',4,2,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(5,1,'T',4,3,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(6,1,'T',5,3,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(7,1,'T',6,3,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(8,1,'T',7,3,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(9,1,'T',8,3,'','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(10,4,'T',3,5,'BTC_DOGE','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(11,4,'T',3,6,'BTC_DASH','2018-03-01 20:25:28',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `exchg_pairs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exchg_taxs`
--

DROP TABLE IF EXISTS `exchg_taxs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchg_taxs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `curr1_id` int(11) DEFAULT NULL,
  `curr2_id` int(11) DEFAULT NULL,
  `tax` decimal(5,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `curr1_id__idx` (`curr1_id`),
  KEY `curr2_id__idx` (`curr2_id`),
  CONSTRAINT `exchg_taxs_ibfk_1` FOREIGN KEY (`curr1_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `exchg_taxs_ibfk_2` FOREIGN KEY (`curr2_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchg_taxs`
--

LOCK TABLES `exchg_taxs` WRITE;
/*!40000 ALTER TABLE `exchg_taxs` DISABLE KEYS */;
INSERT INTO `exchg_taxs` VALUES (1,3,2,0.00),(2,3,1,0.50),(3,4,3,1.00),(4,8,3,1.00);
/*!40000 ALTER TABLE `exchg_taxs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exchgs`
--

DROP TABLE IF EXISTS `exchgs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchgs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) DEFAULT NULL,
  `used` char(1) DEFAULT NULL,
  `url` varchar(55) DEFAULT NULL,
  `tax` decimal(4,3) DEFAULT NULL,
  `fee` decimal(5,3) DEFAULT NULL,
  `API_type` varchar(15) DEFAULT NULL,
  `API` longtext,
  `pkey` longtext,
  `skey` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `url` (`url`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchgs`
--

LOCK TABLES `exchgs` WRITE;
/*!40000 ALTER TABLE `exchgs` DISABLE KEYS */;
INSERT INTO `exchgs` VALUES (1,'WEX','T','wex.nz',0.500,0.000,'btc-e_3','',NULL,NULL),(2,'Livecoin','T','api.livecoin.net',0.200,0.000,'livecoin','exchange/ticker',NULL,NULL),(3,'Cryptsy','F','cryptsy.com',1.000,0.000,'cryptsy','',NULL,NULL),(4,'Poloniex.com','T','poloniex.com',0.200,0.000,'poloniex','',NULL,NULL);
/*!40000 ALTER TABLE `exchgs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fees`
--

DROP TABLE IF EXISTS `fees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fees` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exchg_id` int(11) DEFAULT NULL,
  `dealer_id` int(11) DEFAULT NULL,
  `fee_ed` decimal(4,2) DEFAULT NULL,
  `fee_de` decimal(4,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `exchg_id__idx` (`exchg_id`),
  KEY `dealer_id__idx` (`dealer_id`),
  CONSTRAINT `fees_ibfk_1` FOREIGN KEY (`exchg_id`) REFERENCES `exchgs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fees_ibfk_2` FOREIGN KEY (`dealer_id`) REFERENCES `dealers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fees`
--

LOCK TABLES `fees` WRITE;
/*!40000 ALTER TABLE `fees` DISABLE KEYS */;
INSERT INTO `fees` VALUES (1,1,1,1.00,0.00),(2,2,1,1.00,0.00),(3,3,1,1.00,0.00),(4,4,1,1.00,0.00);
/*!40000 ALTER TABLE `fees` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gifts`
--

DROP TABLE IF EXISTS `gifts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gifts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT NULL,
  `deal_id` int(11) DEFAULT NULL,
  `sum_` decimal(8,2) DEFAULT NULL,
  `gifted` decimal(8,2) DEFAULT NULL,
  `amount` decimal(7,2) DEFAULT NULL,
  `pick` decimal(6,2) DEFAULT NULL,
  `count_` int(11) DEFAULT NULL,
  `on_create` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `deal_id` (`deal_id`),
  KEY `deal_id__idx` (`deal_id`),
  CONSTRAINT `gifts_ibfk_1` FOREIGN KEY (`deal_id`) REFERENCES `deals` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gifts`
--

LOCK TABLES `gifts` WRITE;
/*!40000 ALTER TABLE `gifts` DISABLE KEYS */;
/*!40000 ALTER TABLE `gifts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logs`
--

DROP TABLE IF EXISTS `logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `on_create` datetime DEFAULT NULL,
  `mess` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs`
--

LOCK TABLES `logs` WRITE;
/*!40000 ALTER TABLE `logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `news`
--

DROP TABLE IF EXISTS `news`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `news` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `on_create` datetime DEFAULT NULL,
  `head` varchar(100) DEFAULT NULL,
  `body` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `news`
--

LOCK TABLES `news` WRITE;
/*!40000 ALTER TABLE `news` DISABLE KEYS */;
/*!40000 ALTER TABLE `news` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `news_descrs`
--

DROP TABLE IF EXISTS `news_descrs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `news_descrs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `news_descrs`
--

LOCK TABLES `news_descrs` WRITE;
/*!40000 ALTER TABLE `news_descrs` DISABLE KEYS */;
/*!40000 ALTER TABLE `news_descrs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_` int(11) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `volume_in` decimal(18,10) DEFAULT NULL,
  `volume_out` decimal(18,10) DEFAULT NULL,
  `status` varchar(3) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ref___idx` (`ref_`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`ref_`) REFERENCES `deal_acc_addrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders_stack`
--

DROP TABLE IF EXISTS `orders_stack`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orders_stack` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ref___idx` (`ref_`),
  CONSTRAINT `orders_stack_ibfk_1` FOREIGN KEY (`ref_`) REFERENCES `orders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders_stack`
--

LOCK TABLES `orders_stack` WRITE;
/*!40000 ALTER TABLE `orders_stack` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders_stack` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pay_ins`
--

DROP TABLE IF EXISTS `pay_ins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pay_ins` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_` int(11) DEFAULT NULL,
  `amount` decimal(14,8) DEFAULT NULL,
  `confs` int(11) DEFAULT NULL,
  `txid` varchar(80) DEFAULT NULL,
  `vout` int(11) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `status` varchar(15) DEFAULT NULL,
  `status_mess` varchar(150) DEFAULT NULL,
  `order_id` int(11) DEFAULT NULL,
  `payout_id` int(11) DEFAULT NULL,
  `clients_tran_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ref___idx` (`ref_`),
  KEY `order_id__idx` (`order_id`),
  KEY `payout_id__idx` (`payout_id`),
  KEY `clients_tran_id__idx` (`clients_tran_id`),
  CONSTRAINT `pay_ins_ibfk_1` FOREIGN KEY (`ref_`) REFERENCES `deal_acc_addrs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `pay_ins_ibfk_2` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `pay_ins_ibfk_3` FOREIGN KEY (`payout_id`) REFERENCES `pay_outs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `pay_ins_ibfk_4` FOREIGN KEY (`clients_tran_id`) REFERENCES `clients_trans` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pay_ins`
--

LOCK TABLES `pay_ins` WRITE;
/*!40000 ALTER TABLE `pay_ins` DISABLE KEYS */;
/*!40000 ALTER TABLE `pay_ins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pay_ins_stack`
--

DROP TABLE IF EXISTS `pay_ins_stack`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pay_ins_stack` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_` int(11) DEFAULT NULL,
  `in_proc` int(11) DEFAULT NULL,
  `tries` int(11) DEFAULT NULL,
  `to_refuse` char(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ref___idx` (`ref_`),
  CONSTRAINT `pay_ins_stack_ibfk_1` FOREIGN KEY (`ref_`) REFERENCES `pay_ins` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pay_ins_stack`
--

LOCK TABLES `pay_ins_stack` WRITE;
/*!40000 ALTER TABLE `pay_ins_stack` DISABLE KEYS */;
/*!40000 ALTER TABLE `pay_ins_stack` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pay_ins_unused`
--

DROP TABLE IF EXISTS `pay_ins_unused`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pay_ins_unused` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `amount` decimal(16,8) DEFAULT NULL,
  `confs` int(11) DEFAULT NULL,
  `txid` varchar(80) DEFAULT NULL,
  `vout` int(11) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pay_ins_unused`
--

LOCK TABLES `pay_ins_unused` WRITE;
/*!40000 ALTER TABLE `pay_ins_unused` DISABLE KEYS */;
/*!40000 ALTER TABLE `pay_ins_unused` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pay_outs`
--

DROP TABLE IF EXISTS `pay_outs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pay_outs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_` int(11) DEFAULT NULL,
  `txid` varchar(80) DEFAULT NULL,
  `dealer_acc_id` int(11) DEFAULT NULL,
  `amount` decimal(16,8) DEFAULT NULL,
  `amo_taken` decimal(16,8) DEFAULT NULL,
  `amo_to_pay` decimal(14,8) DEFAULT NULL,
  `amo_gift` decimal(14,8) DEFAULT NULL,
  `amo_partner` decimal(16,8) DEFAULT NULL,
  `amo_in` decimal(16,8) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `status` varchar(15) DEFAULT NULL,
  `tax_mess` longtext,
  `info` longtext,
  `vars` longtext,
  PRIMARY KEY (`id`),
  KEY `ref___idx` (`ref_`),
  KEY `dealer_acc_id__idx` (`dealer_acc_id`),
  CONSTRAINT `pay_outs_ibfk_1` FOREIGN KEY (`ref_`) REFERENCES `deal_accs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `pay_outs_ibfk_2` FOREIGN KEY (`dealer_acc_id`) REFERENCES `dealers_accs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pay_outs`
--

LOCK TABLES `pay_outs` WRITE;
/*!40000 ALTER TABLE `pay_outs` DISABLE KEYS */;
/*!40000 ALTER TABLE `pay_outs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `person_addrs`
--

DROP TABLE IF EXISTS `person_addrs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `person_addrs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pers` int(11) DEFAULT NULL,
  `addr` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pers__idx` (`pers`),
  CONSTRAINT `person_addrs_ibfk_1` FOREIGN KEY (`pers`) REFERENCES `persons` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `person_addrs`
--

LOCK TABLES `person_addrs` WRITE;
/*!40000 ALTER TABLE `person_addrs` DISABLE KEYS */;
/*!40000 ALTER TABLE `person_addrs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `person_recs`
--

DROP TABLE IF EXISTS `person_recs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `person_recs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pers` int(11) DEFAULT NULL,
  `k0` varchar(10) DEFAULT NULL,
  `v0` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pers__idx` (`pers`),
  CONSTRAINT `person_recs_ibfk_1` FOREIGN KEY (`pers`) REFERENCES `persons` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `person_recs`
--

LOCK TABLES `person_recs` WRITE;
/*!40000 ALTER TABLE `person_recs` DISABLE KEYS */;
/*!40000 ALTER TABLE `person_recs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `persons`
--

DROP TABLE IF EXISTS `persons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `persons` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `used` char(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `persons`
--

LOCK TABLES `persons` WRITE;
/*!40000 ALTER TABLE `persons` DISABLE KEYS */;
/*!40000 ALTER TABLE `persons` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recl`
--

DROP TABLE IF EXISTS `recl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `recl` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `on_create` datetime DEFAULT NULL,
  `url` longtext,
  `count_` int(11) DEFAULT NULL,
  `level_` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recl`
--

LOCK TABLES `recl` WRITE;
/*!40000 ALTER TABLE `recl` DISABLE KEYS */;
/*!40000 ALTER TABLE `recl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `site_stats`
--

DROP TABLE IF EXISTS `site_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `site_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `page_` varchar(20) DEFAULT NULL,
  `loads` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `site_stats`
--

LOCK TABLES `site_stats` WRITE;
/*!40000 ALTER TABLE `site_stats` DISABLE KEYS */;
/*!40000 ALTER TABLE `site_stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `systems`
--

DROP TABLE IF EXISTS `systems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `systems` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) DEFAULT NULL,
  `name2` varchar(25) DEFAULT NULL,
  `first_char` varchar(5) DEFAULT NULL,
  `connect_url` varchar(512) DEFAULT NULL,
  `account` varchar(512) DEFAULT NULL,
  `block_time` int(11) DEFAULT NULL,
  `txfee` decimal(10,8) DEFAULT NULL,
  `conf` int(11) DEFAULT NULL,
  `conf_gen` int(11) DEFAULT NULL,
  `from_block` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `connect_url` (`connect_url`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `systems`
--

LOCK TABLES `systems` WRITE;
/*!40000 ALTER TABLE `systems` DISABLE KEYS */;
INSERT INTO `systems` VALUES (1,'Erachain','erachain','7','http://127.0.0.1:9068','7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7',288,0.00010000,2,0,30000);
/*!40000 ALTER TABLE `systems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tokens`
--

DROP TABLE IF EXISTS `tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tokens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `system_id` int(11) DEFAULT NULL,
  `token_key` int(11) DEFAULT NULL,
  `name` varchar(125) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `system_id__idx` (`system_id`),
  CONSTRAINT `tokens_ibfk_1` FOREIGN KEY (`system_id`) REFERENCES `systems` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tokens`
--

LOCK TABLES `tokens` WRITE;
/*!40000 ALTER TABLE `tokens` DISABLE KEYS */;
INSERT INTO `tokens` VALUES (1,1,1,'ERA'),(2,1,2,'COMPU');
/*!40000 ALTER TABLE `tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wallets_stats`
--

DROP TABLE IF EXISTS `wallets_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wallets_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `xcurr_id` int(11) DEFAULT NULL,
  `wallet` varchar(100) DEFAULT NULL,
  `value_in` decimal(16,8) DEFAULT NULL,
  `value_out` decimal(16,8) DEFAULT NULL,
  `value_gen` decimal(16,8) DEFAULT NULL,
  `value_orh` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `xcurr_id__idx` (`xcurr_id`),
  CONSTRAINT `wallets_stats_ibfk_1` FOREIGN KEY (`xcurr_id`) REFERENCES `xcurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wallets_stats`
--

LOCK TABLES `wallets_stats` WRITE;
/*!40000 ALTER TABLE `wallets_stats` DISABLE KEYS */;
/*!40000 ALTER TABLE `wallets_stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `xcurrs`
--

DROP TABLE IF EXISTS `xcurrs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `xcurrs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `curr_id` int(11) DEFAULT NULL,
  `first_char` varchar(5) DEFAULT NULL,
  `as_token` int(11) DEFAULT NULL,
  `balance` decimal(16,8) DEFAULT NULL,
  `deposit` decimal(16,8) DEFAULT NULL,
  `clients_deposit` decimal(16,8) DEFAULT NULL,
  `reserve` decimal(4,2) DEFAULT NULL,
  `connect_url` varchar(99) DEFAULT NULL,
  `block_time` int(11) DEFAULT NULL,
  `txfee` decimal(10,8) DEFAULT NULL,
  `conf` int(11) DEFAULT NULL,
  `conf_gen` int(11) DEFAULT NULL,
  `from_block` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `connect_url` (`connect_url`),
  KEY `curr_id__idx` (`curr_id`),
  CONSTRAINT `xcurrs_ibfk_1` FOREIGN KEY (`curr_id`) REFERENCES `currs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `xcurrs`
--

LOCK TABLES `xcurrs` WRITE;
/*!40000 ALTER TABLE `xcurrs` DISABLE KEYS */;
INSERT INTO `xcurrs` VALUES (1,3,'13',0,0.00000000,0.00000000,0.00000000,0.00,'http://login:password@127.0.0.1:8332',600,0.00070000,1,101,NULL),(2,4,'L',0,0.00000000,0.00000000,0.00000000,0.00,'http://login:password@127.0.0.1:9332',150,0.00500000,3,120,NULL),(3,5,'D9A',0,0.00000000,0.00000000,0.00000000,0.00,'http://login:password@127.0.0.1:9432',30,0.10000000,5,101,NULL),(4,6,'',0,0.00000000,0.00000000,0.00000000,0.00,'http://login:password@127.0.0.1:13332',333,0.00500000,3,101,NULL),(5,7,'EM',0,0.00000000,0.00000000,0.00000000,0.00,'http://login:password@127.0.0.1:14332',550,0.10000000,3,101,NULL),(6,8,'4',0,0.00000000,0.00000000,0.00000000,0.00,'http://login:password@127.0.0.1:11332',450,0.10000000,3,120,NULL),(7,9,NULL,1,0.00000000,0.00000000,0.00000000,0.00,'erachain ERA',0,0.00000000,0,0,NULL),(8,10,NULL,2,0.00000000,0.00000000,0.00000000,0.00,'erachain COMPU',0,0.00000000,0,0,NULL);
/*!40000 ALTER TABLE `xcurrs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `xcurrs_raw_trans`
--

DROP TABLE IF EXISTS `xcurrs_raw_trans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `xcurrs_raw_trans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `xcurr_id` int(11) DEFAULT NULL,
  `txid` varchar(80) DEFAULT NULL,
  `tx_hex` longtext,
  `confs` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `xcurr_id__idx` (`xcurr_id`),
  CONSTRAINT `xcurrs_raw_trans_ibfk_1` FOREIGN KEY (`xcurr_id`) REFERENCES `xcurrs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `xcurrs_raw_trans`
--

LOCK TABLES `xcurrs_raw_trans` WRITE;
/*!40000 ALTER TABLE `xcurrs_raw_trans` DISABLE KEYS */;
/*!40000 ALTER TABLE `xcurrs_raw_trans` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-03-01 21:29:45
