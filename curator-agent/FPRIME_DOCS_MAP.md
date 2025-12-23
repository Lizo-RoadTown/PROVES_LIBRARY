# F' Prime Documentation Map - Verified URLs

**Purpose:** Curated list of F' Prime documentation pages and GitHub component locations for curator extraction.
**Last Updated:** December 22, 2025
**Repository:** `github.com/nasa/fprime` (branch: `devel`)
**Base Docs URL:** `https://nasa.github.io/fprime/`

---

## User Guide & Getting Started

1. **Getting Started** - `https://nasa.github.io/fprime/GettingStarted/README.html`
2. **Installation** - `https://nasa.github.io/fprime/INSTALL.html`
3. **Complete Introduction** - `https://nasa.github.io/fprime/UsersGuide/user/full-intro.html`
4. **Core Constructs** (Ports, Components, Topology) - `https://nasa.github.io/fprime/UsersGuide/user/port-comp-top.html`

---

## Architecture & Design

1. **Software Architecture** - `https://nasa.github.io/fprime/Design/fprime-architecture.html`
2. **OS Layer Description** - `https://nasa.github.io/fprime/UsersGuide/dev/os-docs.html`

---

## Best Practices

1. **Development Process** - `https://nasa.github.io/fprime/UsersGuide/best/development-practice.html`
2. **Rate Groups and Timeliness** - `https://nasa.github.io/fprime/UsersGuide/best/rate-group.html`
3. **Dynamic Memory Management** - `https://nasa.github.io/fprime/UsersGuide/best/dynamic-memory.html`

---

## Ground Data System (GDS)

1. **GDS Introduction** - `https://nasa.github.io/fprime/UsersGuide/gds/gds-introduction.html`
2. **GDS CLI Guide** - `https://nasa.github.io/fprime/UsersGuide/gds/gds-cli.html`
3. **Sequencing** - `https://nasa.github.io/fprime/UsersGuide/gds/seqgen.html`

---

## API References

1. **C++ API Documentation** - `https://nasa.github.io/fprime/UsersGuide/api/c++/html/index.html`
2. **CMake API** - `https://nasa.github.io/fprime/UsersGuide/cmake/cmake-api.html`

---

## GitHub Component Locations

**Note:** For detailed architecture extraction, use GitHub file fetching tools with these paths.

### Drivers (Critical for PROVES Kit Integration)

| Component | Path | Description |
|-----------|------|-------------|
| **LinuxI2cDriver** | `Drv/LinuxI2cDriver/` | Linux I2C device driver (used by PROVES sensors) |
| **LinuxSpiDriver** | `Drv/LinuxSpiDriver/` | Linux SPI device driver (used by PROVES radio/flash) |
| **LinuxGpioDriver** | `Drv/LinuxGpioDriver/` | Linux GPIO pin driver |
| **LinuxSerialDriver** | `Drv/LinuxSerialDriver/` | UART serial driver (used by PROVES GPS) |

### Command & Data Handling

| Component | Path | Description |
|-----------|------|-------------|
| **CmdDispatcher** | `Svc/CmdDispatcher/` | Routes commands to components based on opcode |
| **CmdSequencer** | `Svc/CmdSequencer/` | Executes sequences of commands from files |
| **TlmChan** | `Svc/TlmChan/` | Telemetry storage and retrieval |

### Scheduling & Timing

| Component | Path | Description |
|-----------|------|-------------|
| **RateGroupDriver** | `Svc/RateGroupDriver/` | Periodic task scheduling |
| **ActiveRateGroup** | `Svc/ActiveRateGroup/` | Active component for rate group execution |

### Health Monitoring

| Component | Path | Description |
|-----------|------|-------------|
| **Health** | `Svc/Health/` | Component health monitoring and watchdog |

### File Management

| Component | Path | Description |
|-----------|------|-------------|
| **FileDownlink** | `Svc/FileDownlink/` | File transfer from spacecraft to ground |
| **FileUplink** | `Svc/FileUplink/` | File transfer from ground to spacecraft |

### Parameters

| Component | Path | Description |
|-----------|------|-------------|
| **PrmDb** | `Svc/PrmDb/` | Parameter storage and management |

---

## File Patterns in F' Prime Repository

| Pattern | Glob | Purpose |
|---------|------|---------|
| **Component Definition** | `*.fpp` | FPP (F Prime Prime) component specifications |
| **Component Implementation** | `*Impl.cpp` | C++ implementation files |
| **Component Headers** | `*Impl.hpp` | C++ header files |
| **Unit Tests** | `*Test*.cpp` | Component test files |
| **Topology** | `*Topology.fpp` | System topology definitions |

---

## Extraction Priority for PROVES Kit Context

### Phase 1: Driver Components (Most Critical)
These are what PROVES Kit actually uses:

1. **LinuxI2cDriver** (`Drv/LinuxI2cDriver/`)
   - Extract: Component definition (.fpp), implementation, I2C address handling
   - Why: PROVES sensors (IMU, RTC, Barometer) use I2C
   - Expected findings: I2C bus interface, address configuration, error handling

2. **LinuxSpiDriver** (`Drv/LinuxSpiDriver/`)
   - Extract: Component definition, SPI protocol implementation
   - Why: PROVES radio (SX1262) and flash (W25Q) use SPI
   - Expected findings: SPI bus interface, chip select handling

3. **LinuxSerialDriver** (`Drv/LinuxSerialDriver/`)
   - Extract: UART interface definition
   - Why: PROVES GPS (MAX-M10S) uses UART
   - Expected findings: Serial port configuration, baud rate settings

### Phase 2: Core Service Components
4. **CmdDispatcher** + **TlmChan** (`Svc/CmdDispatcher/`, `Svc/TlmChan/`)
   - Extract: Command routing and telemetry patterns
   - Why: Understanding C&DH flow for PROVES integration

5. **RateGroupDriver** (`Svc/RateGroupDriver/`)
   - Extract: Scheduling patterns
   - Why: Understanding periodic task execution for sensors

### Phase 3: Architecture Documentation
6. **Software Architecture** page
7. **Core Constructs** page
8. **Best Practices** - Rate Groups and Memory Management

---

## Known Risk Areas (from source_registry.yaml)

### I2C Addressing Conflicts
- **Search Paths:** `Drv/LinuxI2cDriver/`, `Drv/I2c/`
- **Keywords:** i2c, address, 0x, conflict
- **Why Important:** PROVES Kit has multiple I2C devices that could conflict

### Rate Group Timing Issues
- **Search Paths:** `Svc/RateGroupDriver/`, `Svc/ActiveRateGroup/`
- **Keywords:** rate, group, timing, overrun
- **Why Important:** Sensor polling timing critical for PROVES

### Memory Allocation Patterns
- **Search Paths:** `Fw/Types/`, `Fw/Buffer/`
- **Keywords:** malloc, static, buffer, allocation
- **Why Important:** CubeSat constrained memory environment

---

## GitHub Fetching Strategy

For components, fetch in this order:
1. **README.md** (if exists) - Component overview
2. **ComponentName.fpp** - Formal component specification
3. **ComponentNameImpl.hpp** - Interface definition
4. **ComponentNameImpl.cpp** - Implementation (sample key methods only)

Example for LinuxI2cDriver:
```
github.com/nasa/fprime/blob/devel/Drv/LinuxI2cDriver/README.md
github.com/nasa/fprime/blob/devel/Drv/LinuxI2cDriver/LinuxI2cDriver.fpp
github.com/nasa/fprime/blob/devel/Drv/LinuxI2cDriver/LinuxI2cDriverImpl.hpp
```

---

## URL Structure Notes

**Documentation (Web):**
- Base: `https://nasa.github.io/fprime/`
- Pattern: `{section}/{page}.html`
- All verified working

**GitHub (Repository):**
- Base: `github.com/nasa/fprime`
- Branch: `devel` (not `main` or `master`)
- Use GitHub file fetching tools, not web scraping

---

## Cross-Reference with PROVES Kit

When extracting F' Prime components, always note:
1. **Is this component used by PROVES Kit?** (check source_registry.yaml)
2. **What PROVES hardware uses this driver?** (reference hardware list)
3. **Are there known conflicts?** (check risk areas)
4. **What interfaces does PROVES need?** (I2C addresses, SPI buses, etc.)

---

**Usage:** Use this map alongside PROVESKIT_DOCS_MAP.md to understand full system architecture.
