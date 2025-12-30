# PRD: Die-Cut Drawing Automation Tool (DieCut Automator)

## Document Information

| Item | Content |
|------|---------|
| Version | 2.0 |
| Created | 2024-12-30 |
| Status | Draft |
| Verified | 2024-12-30 |

---

## Verification Checklist

| Verification Item | Status | Notes |
|-------------------|--------|-------|
| Requirements Completeness | ✅ | Missing items added |
| Edge Cases | ✅ | Exception scenarios defined |
| Algorithm Details | ✅ | Formulas/logic clarified |
| Error Handling | ✅ | Error scenarios added |
| UI/UX Details | ✅ | Interactions defined |
| Data Validation | ✅ | Input validation rules added |
| Technical Feasibility | ✅ | Verification complete |

---

## 1. Product Overview

### 1.1 Product Name
**DieCut Automator** (Die-Cut Drawing Automation Tool)

### 1.2 Product Description
A desktop application that automatically converts DXF drawing files into formats suitable for laser processing and Thomson (cutting/creasing) operations. Automates repetitive drawing modification tasks performed by die-cutting companies to reduce work time and prevent human errors.

### 1.3 Goals
- Reduce drawing modification work time by **70% or more**
- **Minimize** errors caused by manual work
- Produce drawings with consistent quality

### 1.4 Target Users
- CAD operators at die-cutting companies
- Thomson/laser processing drawing personnel

### 1.5 Core Value
```
Input: Original DXF + Job Information
Output: Processing-ready DXF (with bridges, plywood frame, text)
```

---

## 2. Background and Problem Definition

### 2.1 Current Situation
- DXF drawings modified manually
- Repetitive tasks (color classification, bridges, plywood frame creation, etc.)
- CAD in use (DreamCAD 3.5) has no scripting capabilities
- Output quality varies between operators

### 2.2 Problems to Solve

| Problem | Current State | Target State |
|---------|---------------|--------------|
| Work Time | 15-30 min per drawing | 3-5 min per drawing |
| Bridge Consistency | Varies by operator | Rule-based consistency |
| Filename Errors | Manual input mistakes | Auto-generated |
| Plywood Size | Manual calculation | Auto-calculated |

### 2.3 Scope Definition

#### In Scope
- DXF file processing (read/write/modify)
- 2D entity processing (LINE, ARC, CIRCLE, POLYLINE, LWPOLYLINE)
- Single file and batch processing
- Windows desktop application

#### Out of Scope
- 3D entity processing
- Direct DWG file processing (convert to DXF first)
- Cloud/web version
- macOS/Linux support (version 1)

---

## 3. Functional Requirements

### 3.1 Input Configuration

#### 3.1.1 File Input

| ID | Requirement | Priority | Details |
|----|-------------|----------|---------|
| IN-001 | Load DXF file | P0 | Single file selection |
| IN-002 | Load multiple files | P1 | For batch processing |
| IN-003 | Drag and drop support | P1 | Drop on main area |
| IN-004 | Recent files list | P2 | Save up to 10 |

**Supported DXF Versions:**
- R12, R13, R14, R2000, R2004, R2007, R2010, R2013, R2018

**File Validation:**
```
- File existence check
- DXF format validity
- File size limit: 50MB
- Entity count limit: 100,000 (show warning)
```

#### 3.1.2 Job Information Input

| ID | Requirement | Priority | Input Format | Default | Validation Rule |
|----|-------------|----------|--------------|---------|-----------------|
| IN-010 | Date | P0 | YYMMDD | Today's date | 6-digit number |
| IN-011 | Number | P0 | Text | Empty | Required, 1-20 chars |
| IN-012 | Package Name | P0 | Text | Empty | Required, 1-50 chars |
| IN-013 | Front/Back Side | P0 | Radio | Back | Required selection |
| IN-014 | Plate Type | P0 | Radio | Auto Plate | Required selection |

**Bottom Margin by Plate Type:**
```
Copper Plate: 25mm
Auto Plate: 15mm
```

**Character Restrictions:**
```
Allowed: Korean, English, numbers, hyphen (-), underscore (_)
Forbidden: Special characters (\ / : * ? " < > |)
```

#### 3.1.3 Paper Size Settings

| ID | Requirement | Priority | Details |
|----|-------------|----------|---------|
| IN-020 | Paper size dropdown | P0 | Dropdown menu |
| IN-021 | Custom size input | P0 | Width × Height (mm) |
| IN-022 | Save custom size | P1 | Save with name |
| IN-023 | Delete custom size | P1 | Delete saved items |

**Standard Paper Sizes:**

| Name | Width (mm) | Height (mm) | Notes |
|------|------------|-------------|-------|
| Gukjeon | 636 | 939 | Korean standard |
| Guk Half | 636 | 469 | |
| Guk Quarter | 318 | 469 | |
| 4×6 Full | 788 | 1091 | |
| 4×6 Half | 545 | 788 | |
| 4×6 Quarter | 394 | 545 | |
| 46-pan | 394 | 545 | Same as 4×6 Quarter |
| A1 | 594 | 841 | ISO standard |
| A2 | 420 | 594 | ISO standard |
| A3 | 297 | 420 | ISO standard |

**Custom Size Validation:**
```
Minimum: 100 × 100 mm
Maximum: 2000 × 3000 mm
Decimal: Up to 1 digit allowed
```

---

### 3.2 Core Features

#### 3.2.1 Cut/Crease Entity Color Classification

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-001 | Assign cut line color | P0 |
| FN-002 | Assign crease line color | P0 |
| FN-003 | Auto-classify based on rules | P0 |
| FN-004 | Edit classification rules | P1 |
| FN-005 | Handle unclassified entities | P0 |

**Default Colors:**
```
Cut: Red (AutoCAD Color Index: 1, RGB: 255,0,0)
Crease: Blue (AutoCAD Color Index: 5, RGB: 0,0,255)
Plywood: Black (AutoCAD Color Index: 7, RGB: 255,255,255)
Auxiliary: Green (AutoCAD Color Index: 3, RGB: 0,255,0)
```

**Classification Rules (by priority):**
```
Priority 1: Layer name matching
   - Cut: "CUT", "KNIFE", "C", "K", "DIE"
   - Crease: "CREASE", "FOLD", "CR", "F", "SCORE"

Priority 2: Existing color matching
   - Cut: Red range (ACI 1, 10~19)
   - Crease: Blue range (ACI 5, 140~149)

Priority 3: Line type
   - Cut: CONTINUOUS, SOLID
   - Crease: DASHED, CENTER, DOT
```

**Unclassified Entity Handling:**
```
Option A: Process as default (cut)
Option B: Separate to different layer and request user confirmation
Option C: Exclude from processing
→ User configurable (default: B)
```

#### 3.2.2 Automatic Bridge Application

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-010 | Apply bridges to LINE only | P0 |
| FN-011 | Bridge rule engine | P0 |
| FN-012 | Bridge size (gap) setting | P0 |
| FN-013 | Separate cut/crease settings | P1 |
| FN-014 | Bridge position preview | P1 |
| FN-015 | Manual bridge addition | P2 |
| FN-016 | Manual bridge removal | P2 |
| FN-017 | POLYLINE segment processing | P1 |

**Bridge Placement Rules:**

```
┌─────────────────────────────────────────────────────────┐
│ Line Length (L)        │ Bridge Count   │ Placement     │
├─────────────────────────────────────────────────────────┤
│ L < 20mm              │ 0              │ No bridge     │
│ 20mm ≤ L < 50mm       │ 1              │ Center        │
│ 50mm ≤ L              │ N              │ Even spacing  │
│                       │ N = ⌊L/60⌋+1   │ (adjust gap)  │
└─────────────────────────────────────────────────────────┘
```

**Bridge Placement Algorithm (detailed):**

```python
def calculate_bridges(line_length, min_length=20, single_max=50,
                      target_interval=60, gap_size=3, edge_margin=10):
    """
    Calculate bridge positions

    Parameters:
    - line_length: Length of the line (mm)
    - min_length: Minimum length for bridge application (default 20mm)
    - single_max: Maximum length for single bridge (default 50mm)
    - target_interval: Target interval (default 60mm, range 50-70mm)
    - gap_size: Bridge gap size (default 3mm)
    - edge_margin: Minimum distance from line ends (default 10mm)

    Returns:
    - List of bridge center positions (0-1 ratio)
    """

    if line_length < min_length:
        return []  # No bridge

    if line_length < single_max:
        return [0.5]  # 1 at center

    # Effective length (excluding margins at both ends)
    effective_length = line_length - (2 * edge_margin)

    if effective_length <= 0:
        return [0.5]  # If shorter than margin, 1 at center

    # Calculate bridge count
    bridge_count = max(1, round(effective_length / target_interval))

    # Calculate actual interval (adjust within 50-70mm range)
    actual_interval = effective_length / bridge_count

    # Adjust count if interval is out of range
    if actual_interval > 70:
        bridge_count += 1
        actual_interval = effective_length / bridge_count
    elif actual_interval < 50 and bridge_count > 1:
        bridge_count -= 1
        actual_interval = effective_length / bridge_count

    # Calculate bridge positions (ratio)
    positions = []
    for i in range(bridge_count):
        # First bridge position + interval * i
        pos = edge_margin + (actual_interval / 2) + (actual_interval * i)
        positions.append(pos / line_length)

    return positions
```

**Bridge Creation Method:**
```
Original LINE: ────────────────────────────────
                    ↓
With bridges:  ─────────   ─────────   ─────────
                   ↑         ↑         ↑
               gap_size  gap_size  gap_size

Implementation: Delete original LINE and create multiple
      shorter LINEs excluding bridge positions
```

**POLYLINE/LWPOLYLINE Processing:**
```
1. Decompose POLYLINE into individual segments
2. Apply bridges only to straight segments
3. Exclude arc segments from bridges
4. Save decomposed segments as individual LINEs
```

**Bridge Setting Parameters:**

| Parameter | Default | Min | Max | Unit |
|-----------|---------|-----|-----|------|
| Minimum Length | 20 | 10 | 50 | mm |
| Single Max Length | 50 | 30 | 100 | mm |
| Target Interval | 60 | 40 | 100 | mm |
| Gap Size | 3 | 1 | 10 | mm |
| Edge Margin | 10 | 5 | 30 | mm |

#### 3.2.3 Arc Segment Connection

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-020 | Connect based on endpoint distance | P0 |
| FN-021 | Tolerance setting | P0 |
| FN-022 | LINE-LINE connection | P0 |
| FN-023 | LINE-ARC connection | P1 |
| FN-024 | ARC-ARC connection | P1 |
| FN-025 | Connection result report | P1 |

**Connection Algorithm:**

```python
def find_connectable_entities(entities, tolerance=0.1):
    """
    Find connectable entity pairs

    Parameters:
    - entities: Entity list
    - tolerance: Allowed tolerance (default 0.1mm)

    Process:
    1. Extract start/end points of all entities
    2. Search for nearby points using spatial indexing (R-tree, etc.)
    3. Identify point pairs within tolerance
    4. Determine connection possibility
    """

    connections = []

    for i, entity_a in enumerate(entities):
        for j, entity_b in enumerate(entities):
            if i >= j:
                continue

            # Calculate distances between endpoints
            distances = [
                (entity_a.end, entity_b.start),
                (entity_a.end, entity_b.end),
                (entity_a.start, entity_b.start),
                (entity_a.start, entity_b.end)
            ]

            for point_a, point_b in distances:
                dist = calculate_distance(point_a, point_b)
                if dist <= tolerance and dist > 0:
                    connections.append({
                        'entity_a': entity_a,
                        'entity_b': entity_b,
                        'gap': dist,
                        'points': (point_a, point_b)
                    })

    return connections

def merge_entities(entity_a, entity_b, connection_point):
    """
    Merge two entities into one

    LINE + LINE → LINE (if collinear) or POLYLINE
    LINE + ARC → POLYLINE
    ARC + ARC → POLYLINE
    """
    pass
```

**Connection Rules:**
```
1. Distance condition: Distance between two endpoints ≤ tolerance (default 0.1mm)
2. Continuity condition: No sharp direction change on connection (optional)
3. Layer condition: Connect only entities on same layer (optional)
4. Color condition: Connect only entities with same color (optional)
```

**Tolerance Settings:**
```
Default: 0.1mm
Range: 0.01mm ~ 1.0mm
Recommended: 0.05mm ~ 0.2mm
```

#### 3.2.4 Front/Back Side Processing

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-030 | Front: X-axis mirroring | P0 |
| FN-031 | Back: Keep original | P0 |
| FN-032 | Insert front/back text | P0 |
| FN-033 | Text position/style settings | P1 |

**Mirroring Details:**

```
Front Side:
- Mirror axis: Y-axis (vertical line)
- Mirror reference: Drawing center X coordinate
- Transform: Invert X coordinate of all entities
  New X = 2 * Center X - Original X

Back Side:
- No transformation, use original as-is
```

**Mirroring Considerations:**
```
1. Text entities: Re-invert after mirror to remain readable
2. Block references: Apply mirroring inside blocks
3. Hatches: Adjust hatch pattern direction
4. Dimensions: Keep dimension values, mirror position only
```

**Front/Back Text:**
```
Content: "Front" or "Back"
Position: Drawing upper right or designated position in plywood
Height: Default 5mm (configurable: 3-20mm)
Font: Default system font (configurable)
Color: Black (configurable)
```

#### 3.2.5 Straight Knife Insertion

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-040 | Create straight knives on left/right of drawing | P0 |
| FN-041 | Apply bridges to straight knives | P0 |
| FN-042 | Determine straight knife Y position | P0 |
| FN-043 | Support multiple straight knives | P1 |

**Straight Knife Generation Logic:**

```
Purpose: Add extension lines when drawing exceeds paper size

┌──────────────────────────────────────────────┐
│                    Plywood                    │
│  ┌─────────────────────────────────────────┐ │
│  │                                         │ │
│  │              Drawing Area               │ │
│──┼─────────────────────────────────────────┼─│ ← Straight knife
│  │              (Original)                 │ │
│  │                                         │ │
│  └─────────────────────────────────────────┘ │
│                                              │
└──────────────────────────────────────────────┘

Straight knife = Plywood left end ─────── Drawing left + Drawing right ─────── Plywood right end
```

**Straight Knife Y Position Algorithm:**

```python
def determine_straight_knife_y_positions(drawing_entities, paper_height):
    """
    Determine Y position of straight knife

    Method 1: Drawing center Y coordinate (simple)
    Method 2: Y coordinates of major horizontal lines (precise)
    Method 3: User specified
    """

    # Method 1: Center-based
    bbox = calculate_bounding_box(drawing_entities)
    center_y = (bbox.min_y + bbox.max_y) / 2

    return [center_y]

    # Method 2: Major horizontal line detection (advanced)
    horizontal_lines = find_horizontal_lines(drawing_entities)
    major_y_positions = cluster_y_positions(horizontal_lines)

    return major_y_positions
```

**Straight Knife Creation:**
```python
def create_straight_knives(drawing_bbox, paper_bbox, y_positions, bridge_settings):
    """
    Create straight knife LINEs

    Parameters:
    - drawing_bbox: Drawing bounding box
    - paper_bbox: Plywood (paper) bounding box
    - y_positions: Straight knife Y coordinate list
    - bridge_settings: Bridge settings

    Returns:
    - List of LINE entities (with bridges applied)
    """

    knives = []

    for y in y_positions:
        # Left straight knife
        left_knife = Line(
            start=(paper_bbox.min_x, y),
            end=(drawing_bbox.min_x, y)
        )

        # Right straight knife
        right_knife = Line(
            start=(drawing_bbox.max_x, y),
            end=(paper_bbox.max_x, y)
        )

        # Apply bridges
        left_with_bridges = apply_bridges(left_knife, bridge_settings)
        right_with_bridges = apply_bridges(right_knife, bridge_settings)

        knives.extend(left_with_bridges)
        knives.extend(right_with_bridges)

    return knives
```

#### 3.2.6 Plywood Rectangle Generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-050 | Calculate bounding box | P0 |
| FN-051 | Apply margins | P0 |
| FN-052 | Generate plywood rectangle | P0 |
| FN-053 | Adjust drawing position | P0 |
| FN-054 | Plywood layer/color settings | P1 |

**Plywood Size and Drawing Placement:**

```
┌────────────────────────────────────────────┐
│←──────────── Paper Width ─────────────────→│
│                                            │ ↑
│  Top Margin (default 10mm)                 │ │
│  ┌──────────────────────────────────────┐  │ │
│  │                                      │  │ │
│  │                                      │  │ Paper
│  │           Drawing Area               │  │ Height
│  │                                      │  │
│  │                                      │  │
│  └──────────────────────────────────────┘  │
│  Bottom Margin (Copper:25mm / Auto:15mm)   │ │
│                                            │ ↓
└────────────────────────────────────────────┘
  ↑                                        ↑
  Left Margin                          Right Margin
  (default 10mm)                       (default 10mm)
```

**Drawing Position Calculation:**

```python
def calculate_drawing_position(drawing_bbox, paper_size, plate_type, margins):
    """
    Calculate final drawing position

    Parameters:
    - drawing_bbox: Original drawing bounding box
    - paper_size: Paper size (width, height)
    - plate_type: 'copper' or 'auto'
    - margins: Margin settings

    Returns:
    - Offset to move (dx, dy)
    """

    # Bottom margin
    bottom_margin = 25 if plate_type == 'copper' else 15

    # Center horizontally
    drawing_width = drawing_bbox.max_x - drawing_bbox.min_x
    available_width = paper_size.width - margins.left - margins.right
    offset_x = margins.left + (available_width - drawing_width) / 2 - drawing_bbox.min_x

    # Place based on bottom margin
    offset_y = bottom_margin - drawing_bbox.min_y

    return (offset_x, offset_y)
```

**Plywood Rectangle Creation:**
```python
def create_plywood_rectangle(paper_size):
    """
    Create plywood outer rectangle

    Returns:
    - LWPOLYLINE (closed rectangle)
    """

    points = [
        (0, 0),
        (paper_size.width, 0),
        (paper_size.width, paper_size.height),
        (0, paper_size.height),
        (0, 0)  # Closed
    ]

    return LWPolyline(points, layer="PLYWOOD", color=7)
```

**Margin Settings:**

| Margin | Default | Min | Max | Notes |
|--------|---------|-----|-----|-------|
| Top | 10mm | 5mm | 50mm | |
| Bottom (Copper) | 25mm | 20mm | 50mm | Fixed recommended |
| Bottom (Auto) | 15mm | 10mm | 50mm | Fixed recommended |
| Left | 10mm | 5mm | 50mm | |
| Right | 10mm | 5mm | 50mm | |

#### 3.2.7 Text Information Writing

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-060 | Generate job info text | P0 |
| FN-061 | Specify text position | P0 |
| FN-062 | Text style settings | P1 |

**Text Content Format:**
```
{Date}-{Number}-{PackageName} {PaperSize}

Examples:
241230-001-ABC_Package Gukjeon
241230-002-XYZ_Box 4x6Full
241230-003-Test 650x900
```

**Text Position:**
```
Position: Plywood upper left
Coordinates: (margin_left + 5mm, paper_height - margin_top - text_height - 5mm)

┌────────────────────────────────────────────┐
│  241230-001-ABC_Package Gukjeon  ← Text    │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │                                      │  │
```

**Text Attributes:**

| Attribute | Default | Configurable Range |
|-----------|---------|-------------------|
| Height | 5mm | 2-20mm |
| Font | simplex | System SHX fonts |
| Color | Black (7) | ACI 1-255 |
| Rotation | 0° | 0-360° |
| Alignment | Bottom-left | 9 directions |

#### 3.2.8 Unnecessary Element Removal

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-070 | Identify elements outside plywood | P0 |
| FN-071 | Auto-remove external elements | P0 |
| FN-072 | Exclude layer settings | P1 |
| FN-073 | Confirm before removal | P1 |

**Removal Target Identification:**
```python
def identify_elements_to_remove(entities, plywood_bbox, exclude_layers):
    """
    Identify elements to remove

    Removal targets:
    1. Entities completely outside plywood bounding box
    2. Not in exclude layers

    Keep:
    - Plywood rectangle itself
    - Entities inside or on plywood boundary
    - Job info text
    - Entities in exclude layers
    """

    to_remove = []

    for entity in entities:
        entity_bbox = get_entity_bbox(entity)

        # Determine if completely outside
        if is_completely_outside(entity_bbox, plywood_bbox):
            if entity.layer not in exclude_layers:
                to_remove.append(entity)

    return to_remove
```

**Removal Confirmation Options:**
```
- Auto-remove (no confirmation)
- Show list and confirm before removal
- Highlight removal items and confirm
```

#### 3.2.9 File Saving

| ID | Requirement | Priority |
|----|-------------|----------|
| FN-080 | Save as DXF format | P0 |
| FN-081 | Auto-generate filename | P0 |
| FN-082 | Select save path | P0 |
| FN-083 | Set default save path | P1 |
| FN-084 | Overwrite confirmation | P0 |
| FN-085 | Open after save option | P2 |

**Filename Generation Rules:**
```
Format: {Date}-{Number}-{PackageName}-{PaperSize}.dxf

Character substitution:
- Space → Underscore (_)
- Remove special characters: \ / : * ? " < > |
- × → x (multiplication sign)

Example:
Input: Date=241230, Number=001, PackageName=ABC Package, Paper=4×6Full
Output: 241230-001-ABC_Package-4x6Full.dxf
```

**Save DXF Version:**
```
Default: AutoCAD 2010 (AC1024) - Optimal compatibility
Selectable: R12, R2000, R2004, R2007, R2010, R2013, R2018
```

---

### 3.3 Preview and Validation

| ID | Requirement | Priority |
|----|-------------|----------|
| PV-001 | Real-time drawing preview | P0 |
| PV-002 | Zoom in/out | P0 |
| PV-003 | Pan | P0 |
| PV-004 | Fit to view | P0 |
| PV-005 | Before/after comparison | P1 |
| PV-006 | Layer show/hide | P1 |
| PV-007 | Bridge position highlight | P1 |
| PV-008 | Grid display | P2 |

**Preview Controls:**
```
Mouse wheel: Zoom in/out
Mouse drag: Pan
Double click: Fit to view
Right-click menu: Additional options
```

**Comparison Mode:**
```
Split view: Original | Result
Slider: Overlay comparison
Toggle: Switch original/result
```

---

### 3.4 Settings and Presets

| ID | Requirement | Priority |
|----|-------------|----------|
| ST-001 | Save preset | P1 |
| ST-002 | Load preset | P1 |
| ST-003 | Delete preset | P1 |
| ST-004 | Restore defaults | P1 |
| ST-005 | Export/import settings | P2 |

**Preset Contents:**
```
- Bridge settings (interval, size, margin)
- Color settings (cut, crease, plywood)
- Margin settings
- Text style
- Layer mapping rules
- Default save path
```

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NF-001 | File loading time | < 3 sec (1MB) | Timer |
| NF-002 | Automation processing time | < 5 sec (normal drawing) | Timer |
| NF-003 | Large file processing | < 30 sec (10MB) | Timer |
| NF-004 | Memory usage | < 500MB | Monitoring |
| NF-005 | UI responsiveness | < 100ms | Perceived |

### 4.2 Compatibility

| ID | Requirement | Details |
|----|-------------|---------|
| NF-010 | DXF input version | R12 ~ R2018 |
| NF-011 | DXF output version | R2010 (default), selectable |
| NF-012 | Operating system | Windows 10/11 (64bit) |
| NF-013 | Screen resolution | 1280×720 or higher |
| NF-014 | External CAD compatibility | AutoCAD, DreamCAD tested |

### 4.3 Stability

| ID | Requirement | Details |
|----|-------------|---------|
| NF-020 | Crash recovery | Auto-save (1 min interval) |
| NF-021 | Undo | Up to 50 steps |
| NF-022 | Error logging | Detailed log file generation |
| NF-023 | Original preservation | Never modify original file |

### 4.4 Usability

| ID | Requirement | Details |
|----|-------------|---------|
| NF-030 | Language | Korean (default), English (option) |
| NF-031 | Shortcuts | Provide shortcuts for major functions |
| NF-032 | Help | Built-in help and tooltips |
| NF-033 | Learning curve | Basic use within 30 minutes |

---

## 5. Error Handling

### 5.1 Error Scenarios and Responses

| Scenario | Error Message | Response |
|----------|---------------|----------|
| File not found | "File not found" | Show file selection dialog |
| Invalid DXF | "Invalid DXF file" | Show detailed error, prompt another file |
| File size exceeded | "File too large (max 50MB)" | Suggest split or optimize |
| No entities | "No entities to process" | Suggest layer check |
| Save failed | "Failed to save file" | Check permissions, select different path |
| Drawing > Paper | "Drawing larger than paper" | Warn and proceed or adjust size |
| Out of memory | "Out of memory" | Suggest closing other programs |

### 5.2 Validation Checkpoints

```
After file load:
□ DXF parsing success
□ Entity count verification
□ Supported entity type check

Before processing:
□ Required input validation
□ Paper size vs drawing size comparison
□ Layer/color mapping verification

After processing:
□ Result entity validity
□ File save possibility
```

---

## 6. Technology Stack

### 6.1 Confirmed Technologies

| Category | Technology | Version | Notes |
|----------|------------|---------|-------|
| Language | Python | 3.10+ | Use type hints |
| DXF Processing | ezdxf | 1.0+ | Read/write/modify |
| GUI | PyQt6 | 6.4+ | Cross-platform UI |
| Graphics | PyQt6 QPainter | - | Drawing rendering |
| Packaging | PyInstaller | 5.0+ | exe distribution |
| Settings Storage | JSON | - | Human-readable format |
| Logging | logging | Built-in | Standard library |

### 6.2 Project Structure

```
diecut-automator/
├── src/
│   ├── main.py                 # Entry point
│   ├── app.py                  # Application class
│   ├── ui/
│   │   ├── main_window.py      # Main window
│   │   ├── input_panel.py      # Input panel
│   │   ├── preview_widget.py   # Preview widget
│   │   └── dialogs/            # Dialogs
│   ├── core/
│   │   ├── dxf_handler.py      # DXF read/write
│   │   ├── processor.py        # Main processing logic
│   │   ├── bridge.py           # Bridge algorithm
│   │   ├── mirror.py           # Mirroring processing
│   │   ├── merge.py            # Segment connection
│   │   └── geometry.py         # Geometric operations
│   ├── models/
│   │   ├── settings.py         # Settings data model
│   │   ├── job.py              # Job info model
│   │   └── paper.py            # Paper size model
│   └── utils/
│       ├── config.py           # Config management
│       ├── logger.py           # Logging
│       └── validators.py       # Input validation
├── resources/
│   ├── icons/                  # Icons
│   ├── styles/                 # QSS styles
│   └── defaults.json           # Default settings
├── tests/
│   ├── test_bridge.py
│   ├── test_processor.py
│   └── fixtures/               # Test DXF files
├── docs/
│   └── user_manual.md
├── requirements.txt
├── setup.py
└── README.md
```

### 6.3 Dependencies

```
# requirements.txt
ezdxf>=1.0.0
PyQt6>=6.4.0
pyinstaller>=5.0.0
```

---

## 7. User Interface

### 7.1 Main Screen Detailed Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  File(F)  Edit(E)  View(V)  Tools(T)  Settings(S)  Help(H)              │
├─────────────────────────────────────────────────────────────────────────┤
│  [Open] [Save] [Run] | [Zoom+] [Zoom-] [Fit] | [Settings] [Help]        │
├────────────────────────┬────────────────────────────────────────────────┤
│                        │                                                │
│  ┌─ File Info ───────┐ │                                                │
│  │ File: example.dxf │ │                                                │
│  │ Size: 1.2 MB      │ │                                                │
│  │ Entities: 2,345   │ │                                                │
│  └──────────────────┘ │                                                │
│                        │                                                │
│  ┌─ Job Info ────────┐ │            Drawing Preview Area                │
│  │                   │ │                                                │
│  │ Date: [241230  ]  │ │        ┌─────────────────────┐                 │
│  │ Number: [001   ]  │ │        │                     │                 │
│  │ Package Name:     │ │        │    [Drawing View]   │                 │
│  │ [ABC_Package   ]  │ │        │                     │                 │
│  │                   │ │        └─────────────────────┘                 │
│  │ ○ Front  ● Back   │ │                                                │
│  │ ○ Copper ● Auto   │ │     Mouse: Wheel=Zoom, Drag=Pan               │
│  │                   │ │                                                │
│  └──────────────────┘ │                                                │
│                        │                                                │
│  ┌─ Paper Size ──────┐ │                                                │
│  │                   │ │                                                │
│  │ ● Select Standard │ │                                                │
│  │   [Gukjeon    ▼]  │ │                                                │
│  │                   │ │                                                │
│  │ ○ Custom Input    │ │                                                │
│  │   Width:[    ] mm │ │                                                │
│  │   Height:[   ] mm │ │                                                │
│  │                   │ │────────────────────────────────────────────────│
│  └──────────────────┘ │  Tabs: [Original] [Result] [Compare]           │
│                        │                                                │
│  ┌─ Bridge Settings ─┐ │                                                │
│  │ Interval: [60] mm │ │                                                │
│  │ Size: [3   ] mm   │ │                                                │
│  │ [Advanced...]     │ │                                                │
│  └──────────────────┘ │                                                │
│                        │                                                │
│  ┌──────────────────┐ │                                                │
│  │                   │ │                                                │
│  │  [▶ Run Process]  │ │                                                │
│  │                   │ │                                                │
│  └──────────────────┘ │                                                │
│                        │                                                │
├────────────────────────┴────────────────────────────────────────────────┤
│  Ready | Drawing: 636 × 450 mm | Paper: Gukjeon (636 × 939)             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Bridge Advanced Settings Dialog

```
┌─ Bridge Advanced Settings ────────────────────┐
│                                                │
│  ┌─ Basic Settings ────────────────────────┐  │
│  │                                          │  │
│  │  Min Length:        [20    ] mm          │  │
│  │  (No bridge below this length)           │  │
│  │                                          │  │
│  │  Single Bridge Max: [50    ] mm          │  │
│  │  (Single bridge at center up to this)    │  │
│  │                                          │  │
│  │  Target Interval:   [60    ] mm          │  │
│  │  (Auto-adjust within 50-70mm range)      │  │
│  │                                          │  │
│  │  Gap Size:          [3     ] mm          │  │
│  │  (Bridge cut length)                     │  │
│  │                                          │  │
│  │  Edge Margin:       [10    ] mm          │  │
│  │  (Distance from line end to first bridge)│  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  ┌─ Separate Cut/Crease Settings ──────────┐  │
│  │  □ Use separate cut/crease settings     │  │
│  │                                          │  │
│  │     Cut Interval: [60] mm  Gap: [3] mm   │  │
│  │   Crease Interval: [50] mm  Gap: [2] mm  │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│           [Restore Defaults]  [Cancel]  [OK]   │
│                                                │
└────────────────────────────────────────────────┘
```

### 7.3 Detailed Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Workflow                              │
└──────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │  Start  │
    └────┬────┘
         │
         ▼
    ┌─────────────┐     ┌─────────────────────────────────┐
    │ Open DXF    │────→│ Validate: file exists, format,  │
    │ File        │     │ size                            │
    └─────┬───────┘     └─────────────────────────────────┘
          │                            │
          │                            ▼ On failure
          │                    ┌───────────────┐
          │                    │ Error message │
          │                    │ Select again  │
          │                    └───────────────┘
          ▼
    ┌─────────────┐
    │ Show Drawing│ ← Auto-execute
    │ Preview     │
    └─────┬───────┘
          │
          ▼
    ┌─────────────┐     ┌─────────────────────────────────┐
    │ Enter Job   │────→│ Required: Date, Number, Package │
    │ Info        │     │ Optional: Front/Back, Plate Type│
    └─────┬───────┘     └─────────────────────────────────┘
          │
          ▼
    ┌─────────────┐     ┌─────────────────────────────────┐
    │ Set Paper   │────→│ Select standard or custom input │
    │ Size        │     └─────────────────────────────────┘
    └─────┬───────┘
          │
          ▼
    ┌─────────────┐     ┌─────────────────────────────────┐
    │ Bridge      │────→│ Use defaults or advanced setup  │
    │ Settings    │     └─────────────────────────────────┘
    └─────┬───────┘
          │
          ▼
    ┌─────────────┐
    │ Click [Run  │
    │  Process]   │
    └─────┬───────┘
          │
          ▼
    ┌─────────────────────────────────────────────────────┐
    │                    Processing Steps                  │
    │                                                     │
    │  1. Cut/Crease color classification                 │
    │  2. Front side mirroring                            │
    │  3. Segment connection (optional)                   │
    │  4. Drawing position adjustment                     │
    │  5. Bridge application                              │
    │  6. Straight knife insertion                        │
    │  7. Plywood rectangle generation                    │
    │  8. Text insertion                                  │
    │  9. External element removal                        │
    │                                                     │
    │  [■■■■■■■■░░] 80% - Applying bridges...            │
    │                                                     │
    └─────────────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────┐
    │ Result      │ ← Tab auto-switch
    │ Preview     │
    └─────┬───────┘
          │
          ▼
    ┌─────────────┐     ┌─────────────────────────────────┐
    │ Verify      │────→│ If issues: adjust settings, re-run│
    │ Result      │     └─────────────────────────────────┘
    └─────┬───────┘
          │
          ▼
    ┌─────────────┐     ┌─────────────────────────────────┐
    │ Save File   │────→│ Auto-generated filename         │
    │             │     │ Select path (default: last path)│
    └─────┬───────┘     └─────────────────────────────────┘
          │
          ▼
    ┌─────────┐
    │  Done   │
    └─────────┘
```

### 7.4 Shortcuts

| Shortcut | Function |
|----------|----------|
| Ctrl+O | Open file |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save as |
| F5 | Run process |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+0 | Fit to view |
| F1 | Help |

---

## 8. Data Model

### 8.1 Settings File (settings.json)

```json
{
  "version": "1.0",
  "bridge": {
    "min_length": 20,
    "single_bridge_max": 50,
    "target_interval": 60,
    "gap_size": 3,
    "edge_margin": 10,
    "separate_cut_crease": false,
    "cut_settings": {
      "interval": 60,
      "gap_size": 3
    },
    "crease_settings": {
      "interval": 50,
      "gap_size": 2
    }
  },
  "colors": {
    "cut": {"aci": 1, "rgb": [255, 0, 0]},
    "crease": {"aci": 5, "rgb": [0, 0, 255]},
    "plywood": {"aci": 7, "rgb": [255, 255, 255]},
    "auxiliary": {"aci": 3, "rgb": [0, 255, 0]}
  },
  "margins": {
    "top": 10,
    "bottom_copper": 25,
    "bottom_auto": 15,
    "left": 10,
    "right": 10
  },
  "text": {
    "height": 5,
    "font": "simplex",
    "color": 7
  },
  "merge": {
    "enabled": true,
    "tolerance": 0.1,
    "same_layer_only": true,
    "same_color_only": true
  },
  "layer_mapping": {
    "cut": ["CUT", "KNIFE", "C", "K", "DIE"],
    "crease": ["CREASE", "FOLD", "CR", "F", "SCORE"]
  },
  "unclassified_handling": "separate",
  "paper_sizes": {
    "standard": {
      "Gukjeon": {"width": 636, "height": 939},
      "Guk Half": {"width": 636, "height": 469},
      "Guk Quarter": {"width": 318, "height": 469},
      "4x6 Full": {"width": 788, "height": 1091},
      "4x6 Half": {"width": 545, "height": 788},
      "4x6 Quarter": {"width": 394, "height": 545}
    },
    "custom": []
  },
  "output": {
    "dxf_version": "AC1024",
    "default_path": "",
    "open_after_save": false
  },
  "recent_files": [],
  "presets": []
}
```

### 8.2 Job Session

```python
@dataclass
class JobSession:
    # Input file
    input_file: str
    input_entities: List[Entity]

    # Job info
    date: str          # YYMMDD
    number: str        # Job number
    package_name: str  # Package name
    side: str          # 'front' or 'back'
    plate_type: str    # 'copper' or 'auto'

    # Paper settings
    paper_name: str
    paper_width: float
    paper_height: float

    # Processing result
    output_entities: List[Entity]
    output_file: str

    # Meta info
    created_at: datetime
    processed_at: datetime
    status: str        # 'pending', 'processing', 'completed', 'error'
    error_message: str
```

---

## 9. Development Roadmap

### Phase 1: MVP (4 weeks)

**Goal: Core functionality verification**

| Week | Task | Details | Deliverable |
|------|------|---------|-------------|
| 1 | Project setup | Environment config, basic structure, DXF read/write | Project skeleton |
| 2 | Basic UI + Color/Mirror | Main window, input panel, color classification, mirroring | Basic UI working |
| 3 | Bridge + Plywood | Bridge algorithm, plywood rectangle, text | Core processing complete |
| 4 | Integration + Testing | Full workflow, saving, bug fixes | MVP release |

**MVP Feature Checklist:**
- [x] DXF file open/save
- [x] Job info input (date, number, package name, front/back, plate type)
- [x] Paper size (standard + custom input)
- [x] Cut/Crease color classification
- [x] Automatic bridge application
- [x] Front/Back mirroring
- [x] Plywood rectangle generation
- [x] Text info insertion
- [x] External element removal
- [x] Auto filename save
- [x] Basic preview

### Phase 2: Enhancement (2 weeks)

| Task | Details |
|------|---------|
| Segment Connection | Arc segment connection feature |
| Straight Knife | Left/right straight knife insertion (with bridges) |
| Preview Enhancement | Zoom/pan, before/after comparison |
| Setting Presets | Save/load |
| Paper Size Management | Add/edit/delete |

### Phase 3: Advanced (2 weeks)

| Task | Details |
|------|---------|
| Batch Processing | Multi-file bulk processing |
| Manual Bridge | Add/remove editing |
| Undo/Redo | Undo/Redo function |
| Shortcuts | Major function shortcuts |
| User Manual | Help documentation |

---

## 10. Test Plan

### 10.1 Unit Tests

| Module | Test Items |
|--------|------------|
| bridge.py | Bridge count by length, position calculation accuracy |
| geometry.py | Bounding box, distance calculation, mirror transform |
| merge.py | Segment connection detection, merge result |
| validators.py | Input validation (date, filename, etc.) |

### 10.2 Integration Tests

| Scenario | Verification Items |
|----------|---------------------|
| Full workflow | Input→Processing→Save normal operation |
| DXF version compatibility | R12~R2018 file processing |
| Large files | 10MB+ file processing time, memory |
| Special cases | Empty drawing, single entity, curves only |

### 10.3 User Acceptance Testing (UAT)

| Test | Criteria |
|------|----------|
| Real work application | Test with actual work drawings |
| Output quality | Open and verify in CAD |
| Work time comparison | Time reduction vs manual work |
| Feedback incorporation | Collect user opinions |

---

## 11. Risk Factors and Mitigation Strategies

| Risk Factor | Impact | Probability | Mitigation Strategy |
|-------------|--------|-------------|---------------------|
| DXF compatibility issues | High | Medium | Test various versions, use latest ezdxf |
| Bridge quality dissatisfaction | Medium | Medium | Detailed parameters, manual editing function |
| Complex drawing processing failure | Medium | Low | Enhanced exception handling, partial manual mode |
| Performance issues (large files) | Low | Low | Progress display, optimization |
| User learning curve | Low | Medium | Intuitive UI, help/tooltips |

---

## 12. Success Metrics (KPI)

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Work time per drawing | 15-30 min | 3-5 min | Timer comparison |
| Work error rate | 5-10% | <1% | Rework count |
| Bridge consistency | Uneven | Rule-based uniform | Visual inspection |
| User satisfaction | - | 4.0/5.0 | Survey |
| Daily processing volume | 20-30 | 50+ | Work log |

---

## 13. Appendix

### 13.1 Glossary

| Term | English | Description |
|------|---------|-------------|
| Cut Line | Cut Line | Line for cutting product (laser/Thomson cutting) |
| Crease Line | Crease Line | Line for folding (creasing, scoring) |
| Bridge | Bridge | Breaking line to create connection points, gap |
| Front Side | Front Side | Drawing based on print side (front) |
| Back Side | Back Side | Drawing based on back (rear) |
| Copper Plate | Copper Plate | For copper plate work (bottom margin 25mm) |
| Auto Plate | Auto Plate | For auto manufacturing (bottom margin 15mm) |
| Paper Size Chart | Paper Size Chart | Standard print paper size table |
| Plywood | Plywood | Outer frame rectangle |
| Straight Knife | Straight Knife | Drawing left/right extension line |
| Thomson | Thomson | Die-cut processing method |
| Bounding Box | Bounding Box | Minimum enclosing rectangle |

### 13.2 DXF Entity Types

| Type | Description | Bridge Applied |
|------|-------------|----------------|
| LINE | Straight line | ○ |
| ARC | Arc | × |
| CIRCLE | Circle | × |
| POLYLINE | Polyline (2D) | Straight segments only |
| LWPOLYLINE | Lightweight polyline | Straight segments only |
| SPLINE | Spline | × |
| ELLIPSE | Ellipse | × |
| TEXT | Single-line text | - |
| MTEXT | Multi-line text | - |

### 13.3 AutoCAD Color Index (ACI) Reference

| ACI | Color | Usage (Default) |
|-----|-------|-----------------|
| 1 | Red | Cut line |
| 2 | Yellow | - |
| 3 | Green | Auxiliary line |
| 4 | Cyan | - |
| 5 | Blue | Crease line |
| 6 | Magenta | - |
| 7 | White/Black | Plywood, text |

### 13.4 References

- ezdxf official docs: https://ezdxf.readthedocs.io/
- PyQt6 docs: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- DXF reference (Autodesk): https://help.autodesk.com/view/OARX/2024/ENU/?guid=GUID-235B22E0-A567-4CF6-92D3-38A2306D73F3

---

## 14. Change History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-12-30 | Initial draft | - |
| 2.0 | 2024-12-30 | Verification and details | - |
|     |            | - Algorithm details added | |
|     |            | - Error handling scenarios added | |
|     |            | - UI details | |
|     |            | - Validation rules added | |
|     |            | - Edge cases defined | |

---

## 15. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Tech Lead | | | |
| QA Lead | | | |

---

*End of Document*
