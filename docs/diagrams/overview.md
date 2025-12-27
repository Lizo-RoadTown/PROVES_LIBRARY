---
layout: article
title: Dependency Overview
---

# Dependency Overview

Complete inventory of all 45+ dependencies found in F´ I2C Driver and PROVES Kit Power Management documentation.

[← Back to Home](../index.html)

---

## Quick Terminology Guide

**Dependency** - When one component needs another component to work
- Example: "The IMU sensor depends on power" means if power fails, IMU fails too

**F´ (F Prime)** - NASA's flight software framework used on many spacecraft

**I2C** - Communication protocol that lets microcontrollers talk to sensors (like USB but for embedded systems)

**PROVES Kit** - University CubeSat platform with standardized hardware modules

**Load Switch** - Electronic switch that turns power on/off to different components

**Device Manager** - Software layer that handles talking to hardware sensors

**Bus Driver** - Low-level software that manages the I2C communication protocol

---

## F´ I2C Driver Dependencies

### Software Architecture

**What you're looking at:** How software layers stack on top of each other to talk to a sensor. Each layer only talks to the layer directly below it.

```mermaid
flowchart TB
    APP[Application Components<br/>Your mission code that needs sensor data]

    DM[ImuManager - Device Manager<br/>Knows how to talk to the IMU sensor<br/>Uses: busWriteRead, busWrite ports<br/>Returns: ImuData, GeometricVector3]

    BD[LinuxI2cDriver - Bus Driver<br/>Low-level I2C communication<br/>Implements: Drv.I2c interface<br/>Returns: I2cStatus success/error codes]

    I2C_BUS[I2C Hardware Bus<br/>/dev/i2c-1<br/>Physical wires: SDA and SCL]

    HW[MPU6050 IMU Sensor<br/>Hardware device at address 0x68<br/>Measures acceleration and rotation]

    APP -->|"1. Requests sensor data"| DM
    DM -->|"2. Calls I2C operations"| BD
    BD -->|"3. Sends electrical signals"| I2C_BUS
    I2C_BUS -->|"4. Physical connection"| HW

    style APP fill:#e1f5ff
    style DM fill:#fff4e1
    style BD fill:#f0e1ff
    style I2C_BUS fill:#ffe0b2
    style HW fill:#ffebee
```

**Key insight:** If any layer fails, all layers above it fail too. This is why dependencies matter!

### Configuration Dependencies

**What you're looking at:** Three types of configuration that all need to match up correctly.

```mermaid
flowchart TB
    subgraph BUILD["Build System - Compiles the code"]
        FPUTIL[fprime-util<br/>Build command]
        FPP[FPP files<br/>Component definitions]
    end

    subgraph TOPO["System Configuration - How components connect"]
        TOPO_FILE[topology.fpp<br/>Defines which components exist]
        CONFIG[configureTopology function<br/>Sets up connections at startup]
    end

    subgraph DEVICE["Hardware Configuration - Device settings"]
        ADDR[I2C Address: 0x68<br/>How to find the IMU on the bus]
        REGS[IMU Register Addresses<br/>RESET: 0x00, CONFIG: 0x01, DATA: 0x10]
        VALS[Register Values<br/>What to write to configure the sensor]
    end

    FPUTIL -->|"Compiles"| TOPO_FILE
    FPP -->|"Generates code for"| TOPO_FILE
    TOPO_FILE -->|"Used by"| CONFIG
    CONFIG -->|"Must set correct"| ADDR
    ADDR -->|"Comes from sensor datasheet"| REGS
    REGS -->|"Require correct"| VALS

    style BUILD fill:#e8f5e9
    style TOPO fill:#fff3e0
    style DEVICE fill:#fce4ec
```

**Why this matters:** If the I2C address in code (0x68) doesn't match the hardware's actual address, communication fails silently.

---

## PROVES Kit Load Switch Dependencies

### Power Control Architecture

**What you're looking at:** How the PROVES Kit software controls power to different subsystems.

```mermaid
flowchart TB
    LSM[LoadSwitchManager<br/>Main power control class<br/>Written in Python]

    subgraph TOOLS["Software Tools It Uses"]
        DIO[digitalio.DigitalInOut<br/>Controls GPIO pins]
        LOGGER[Logger<br/>Records events]
        STATE[switch_states dict<br/>Tracks on/off status]
    end

    subgraph DEVICES["Hardware It Powers"]
        RADIO[Radio<br/>board.RADIO_ENABLE]
        IMU[IMU Sensor<br/>board.IMU_ENABLE]
        MAG[Magnetometer<br/>board.MAG_ENABLE]
        CAM[Camera<br/>board.CAMERA_ENABLE]
    end

    LSM -->|Uses| DIO
    LSM -->|Uses| LOGGER
    LSM -->|Uses| STATE

    LSM -->|Controls power to| RADIO
    LSM -->|Controls power to| IMU
    LSM -->|Controls power to| MAG
    LSM -->|Controls power to| CAM

    style LSM fill:#e1f5ff
    style TOOLS fill:#fff9c4
    style DEVICES fill:#ffebee
```

**Key insight:** The LoadSwitchManager is the single point of control for all subsystem power. If it fails, you can't turn anything on or off.

### Configuration Flow

```mermaid
sequenceDiagram
    participant User
    participant LSM as LoadSwitchManager
    participant Pin as DigitalInOut
    participant HW as Hardware

    User->>LSM: Initialize with switches dict
    LSM->>Pin: Create DigitalInOut(board.IMU_ENABLE)
    LSM->>LSM: Set enable_logic (active high/low)
    LSM->>LSM: Initialize switch_states dict

    User->>LSM: turn_on("imu")
    LSM->>Pin: Set pin HIGH (if active high)
    Pin->>HW: Enable power to IMU
    LSM->>LSM: Update switch_states["imu"] = True
    LSM-->>User: Return True (success)

    User->>LSM: get_switch_state("imu")
    LSM->>LSM: Query switch_states dict
    LSM-->>User: Return True (powered)
```

---

## Dependency Statistics

### By Category

| Category | F´ Count | PROVES Kit Count | Total |
|----------|----------|------------------|-------|
| **Software Dependencies** | 9 | 6 | 15 |
| **Hardware Dependencies** | 4 | 5 | 9 |
| **Configuration Dependencies** | 5 | 3 | 8 |
| **Build System Dependencies** | 3 | 0 | 3 |
| **Data Type Dependencies** | 4 | 0 | 4 |
| **State Management Dependencies** | 0 | 3 | 3 |
| **TOTAL** | 25 | 17 | **42** |

### By Criticality

```mermaid
pie title Dependency Criticality Distribution
    "HIGH" : 28
    "MEDIUM" : 11
    "LOW" : 3
```

### By Relationship Type

| Relationship Type | Count | Examples |
|-------------------|-------|----------|
| **requires** | 23 | Device Manager requires Bus Driver |
| **enables** | 7 | Load Switch enables IMU power |
| **depends_on** | 6 | Application depends_on Device Manager |
| **controls** | 5 | LoadSwitchManager controls hardware pins |
| **implements** | 1 | ZephyrI2cDriver implements Drv.I2c |

---

## Source Location Coverage

Every dependency tracked with precise source locations:

### F´ Documentation Coverage
- **File:** `nasa/fprime/docs/how-to/develop-device-driver.md`
- **Lines Analyzed:** 411
- **Dependencies Found:** 25
- **Average Density:** 1 dependency per 16.4 lines

### PROVES Kit Documentation Coverage
- **File:** `proveskit/pysquared/docs/load_switch.md`
- **Lines Analyzed:** 154
- **Dependencies Found:** 17
- **Average Density:** 1 dependency per 9.1 lines

---

## Navigation

- [← Back to Home](../index.html)
- [Next: Cross-System Dependencies ->](cross-system.html)

---

**Analysis Method:** Manual annotation with line-by-line review
**Confidence Level:** High (human-verified)
**Date:** December 20, 2024
