# PROVES Kit Documentation Map - Complete Structure from mkdocs.yml

**Purpose:** Complete documentation map from authoritative mkdocs.yml configuration.
**Last Updated:** December 22, 2025
**Base URL:** `https://docs.proveskit.space/en/latest/`
**Source:** `github.com/proveskit/Documentation/mkdocs.yml`

---

## Home & Overview

1. **Welcome** - `index.md`
2. **Overview** - `overview/overview.md`
3. **Design Philosophy** - `overview/design_philosophy.md`
4. **Kit Elements** - `overview/kit_elements.md`
5. **The Pleiades Five** - `overview/the_pleiades_five.md`

---

## Hardware Documentation

**Hardware Index:** `core_documentation/hardware/index.md`

**Component Pages:**
1. **PROVES Prime** - `core_documentation/hardware/proves_prime.md`
2. **Battery Board** - `core_documentation/hardware/battery_board.md`
3. **Flight Control Board** - `core_documentation/hardware/FC_board.md`
4. **1U Structure** - `core_documentation/hardware/1U_structure.md`
5. **XY Solar Panels** - `core_documentation/hardware/XY_solar_board.md`
6. **Z Solar Panels** - `core_documentation/hardware/Z_solar_board.md`
7. **FlatSat Dev Board** - `core_documentation/hardware/flatsat_dev_board.md`

---

## Software Documentation

**Software Index:** `core_documentation/software/index.md`

**Software Module Pages:**
1. **pysquared.py** - `core_documentation/software/pysquared.md`
2. **functions.py** - `core_documentation/software/functions.md`
3. **big_data.py** - `core_documentation/software/big_data.md`
4. **cdh.py** (Command & Data Handling) - `core_documentation/software/cdh.md`
5. **payload.py** - `core_documentation/software/payload.md`
6. **detumble.py** - `core_documentation/software/detumble.md`

**Development Resources:**
- **Software Dev Diary** - `core_documentation/software/software-dev-diary.md`
- **Battery PicoSDK** - `core_documentation/software/batt-pico-sdk.md`
- **RMF9x Radio Usage** - `core_documentation/software/rfm_radio_usage.md`

---

## F' Prime Integration

**Tutorial:**
- **fprime-proves Tutorial** - `quick_start/fprime-proves_tutorial.md`
  - Shows F' Prime framework integration
  - Tutorial-focused, not architectural reference

---

## Quick Start Guides

**Quick Start Index:** `quick_start/index.md`

1. **CubeSat Fundamentals** - `quick_start/cubesat_fundamentals.md`
2. **Getting Started with PROVES** - `quick_start/proves_quick_start.md`
3. **Contact an Orbiting Satellite** - `quick_start/contacting_proves.md`
4. **Becoming a Contributor** - `quick_start/becoming_contributor.md`

**Developer Guides:**
- **Dev Guide Index** - `quick_start/dev-guides/index.md`
- **Linux Dev Guide** - `quick_start/dev-guides/dev-guide-linux.md`
- **Windows Dev Guide** - `quick_start/dev-guides/dev-guide-windows.md`
- **Mac Dev Guide** - `quick_start/dev-guides/dev-guide-macos.md`
- **REPL Function Test** - `quick_start/dev-guides/dev-guide-repl-function-tests.md`

---

## Testing Documentation

**Testing Index:** `core_documentation/testing/index.md`

1. **Testing Overview** - `core_documentation/testing/testing_overview.md`
2. **Testing Procedures** - `core_documentation/testing/testing_procedures.md`
3. **Testing Results** - `core_documentation/testing/testing_results.md`

---

## Assembly Guides

### Assembly Guide (Original)
**Index:** `assembly_guide/introduction.md`

**Chapters:**
1. **Chapter 0: Parts & Tools** - `assembly_guide/ch_0_parts_tools.md`
2. **Chapter 1: Battery Board** - `assembly_guide/ch_1_eps.md`
3. **Chapter 2: Feet & Heater** - `assembly_guide/ch_2_feet.md`
4. **Chapter 3: Solar Boards** - `assembly_guide/ch_3_solar.md`
5. **Chapter 4: Flight Controller** - `assembly_guide/ch_4_fc.md`
6. **Chapter 5: Antenna** - `assembly_guide/ch_5_antenna.md`
7. **Chapter 6: Structure** - `assembly_guide/ch_6_structure.md`
8. **Chapter 7: Testing** - `assembly_guide/ch_7_testing/index.md`
   - Solar Board Testing: `assembly_guide/ch_7_testing/solar_board_testing.md`
   - Battery Board Testing: `assembly_guide/ch_7_testing/battery_board_testing.md`
   - Flight Controller Testing: `assembly_guide/ch_7_testing/flight_computer_testing.md`
   - FlatSat Testing: `assembly_guide/ch_7_testing/flatsat_testing.md`
9. **Chapter 8: Integration** - `assembly_guide/ch_8_integration.md`
10. **Chapter 9: Final Tests** - `assembly_guide/ch_9_final_tests.md`

### Assembly Guide V3 (Latest)
1. **Chapter 0: Parts & Tools** - `Assembly_Guide_V3/Chapter_0.md`
2. **Chapter 1: Flight Controller** - `Assembly_Guide_V3/Chapter_1.md`
3. **Chapter 2: Face Assembly** - `Assembly_Guide_V3/Chapter_2.md`
4. **Chapter 3: Power Stop** - `Assembly_Guide_V3/Chapter_3.md`
5. **Chapter 4: Battery Board** - `Assembly_Guide_V3/Chapter_4.md`
6. **Chapter 5: Antenna Board** - `Assembly_Guide_V3/Chapter_5.md`
7. **Chapter 6: Integration** - `Assembly_Guide_V3/Chapter_6.md`
8. **Chapter 7: Final Check** - `Assembly_Guide_V3/Chapter_7.md`

---

## Legacy Documentation

**Location:** `core_documentation/legacy/`

1. **Original Pleiades Proposal** - `core_documentation/legacy/original_pleiades_proposal.md`
2. **Yearling-1 Block Diagram** - `core_documentation/legacy/yearling_1_block_diagram.md`
3. **Blue Dawn Hackathon** - `core_documentation/legacy/blue_dawn.md`
4. **Yearling Software Sword** - `core_documentation/legacy/yearling_software_sword.md`

---

## Mission Operations & Programmatic

- **Mission Operations Index** - `core_documentation/mission_operations/index.md`
- **Programmatic Index** - `core_documentation/programatic/index.md`

---

## Publications

- **Publications** - `publications.md`

---

## Quick Reference

- **Quick Reference Card** - `core_documentation/quick_reference.md`

---

## Extraction Priority Order

**Recommended sequence for curator:**

### Phase 1: Hardware Foundation
1. Start: Hardware Overview (get component list)
2. Extract: PROVES Prime (main board)
3. Extract: Flight Control Board (F' Prime integration likely here)
4. Extract: Battery Board (power management)

### Phase 2: F' Prime Integration
5. Extract: fprime-proves Tutorial (understand F' Prime usage)

### Phase 3: Software Architecture
6. Extract: Software Overview
7. Extract: pysquared.py (main flight software)
8. Extract: cdh.py (command & data handling)

### Phase 4: Specific Components
9. Extract: Remaining hardware (solar panels, structure, etc.)
10. Extract: Remaining software modules (payload, detumble, etc.)

---

## URL Structure Notes

**✅ Correct Format:**
- Base: `https://docs.proveskit.space/en/latest/`
- Paths use: `lowercase_with_underscores/`
- Example: `core_documentation/hardware/proves_prime/`

**❌ Incorrect Format (returns 404):**
- ~~`Core-Documentation/Hardware/PROVES-Prime/`~~ (capitals, hyphens)
- ~~`Core_Documentation/Hardware/`~~ (mixed case)

---

## Expected Extraction Content

### Hardware Pages Should Contain:
- Component names and part numbers
- I2C/SPI/UART bus addresses
- Interface connections between boards
- Power requirements and distribution
- Sensor types and specifications

### Software Pages Should Contain:
- Module dependencies
- F' Prime component usage
- Communication protocols
- Command structures
- Data flow patterns

### F' Prime Tutorial Should Contain:
- Which F' Prime components PROVES uses
- Integration patterns
- Dependencies on F' Prime drivers
- Build/deployment information

---

**Usage:** Give this map to curator to avoid expensive URL guessing.
