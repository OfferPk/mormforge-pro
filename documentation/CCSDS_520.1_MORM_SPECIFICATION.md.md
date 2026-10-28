# CCSDS 520.1-P-1.1 Mission Operations Reference Model (MORM) Specification

## Technical Architecture, Standard Interaction Patterns & MAL Message Semantics

### 1\. Executive Summary & Purpose

The **Mission Operations Reference Model (MORM)**, codified in **CCSDS 520.1-P-1.1 (Pink Book, Issue 1.1, May 2026\)** and **CCSDS 520.1-M-1**, defines the common architectural framework for Mission Operations (MO) services across international space agencies, including NASA, ESA, JAXA, DLR, and commercial spaceflight operators.

Space missions have historically suffered from tight coupling between flight software applications, mission planning tools, telemetry systems, and specific underlying communication technologies. The MO Reference Model establishes a Service-Oriented Architecture (SOA) that decouples space mission operational functions from underlying software languages, operating systems, and network protocols.

---

### 2\. Four-Layer Architectural Model

\+-----------------------------------------------------------------------------------+

\|                            APPLICATION LAYER                                      \|

\|   Mission Planning & Scheduling \&bull; Flight Dynamics \&bull; FDIR \&bull; Telemetry Engine   \|

\+-----------------------------------------------------------------------------------+

                                         \|

                                         v

\+-----------------------------------------------------------------------------------+

\|                         COMMON SERVICES LAYER                                     \|

\|   Directory Service \&bull; Interaction / Event Service \&bull; Action Service \&bull; Login     \|

\+-----------------------------------------------------------------------------------+

                                         \|

                                         v

\+-----------------------------------------------------------------------------------+

\|                   MESSAGE ABSTRACTION LAYER (MAL \- CCSDS 521.0-B-2)               \|

\|   Standard Interaction Patterns (SIP) \&bull; Abstract Data Types \&bull; Error Taxonomy  \|

\+-----------------------------------------------------------------------------------+

                                         \|

                                         v

\+-----------------------------------------------------------------------------------+

\|                        TECHNOLOGY MAPPING LAYER                                   \|

\|   Transport Bindings (TCP/IP, Space Packet, ZeroMQ) \&bull; Encodings (XML, Binary)  \|

\+-----------------------------------------------------------------------------------+

---

### 3\. Six Standard Interaction Patterns (SIP)

The Message Abstraction Layer defines exactly six fundamental communication patterns (CCSDS 520.1 Section 4.3):

1. **Send Pattern (SIP-1)**:  
     
   - One-way asynchronous communication (`Consumer` \$\\rightarrow\$ `Provider`).  
   - Unacknowledged fire-and-forget message for telemetry samples or status heartbeats.

   

2. **Submit Pattern (SIP-2)**:  
     
   - Two-way synchronous/asynchronous command submission.  
   - Stage 1: `SUBMIT_REQ` \$\\rightarrow\$ Stage 2: `SUBMIT_ACK` (or MAL Error).

   

3. **Request Pattern (SIP-3)**:  
     
   - Two-way query/response pattern.  
   - Stage 1: `REQUEST_REQ` \$\\rightarrow\$ Stage 2: `REQUEST_RESP` containing queried state.

   

4. **Invoke Pattern (SIP-4)**:  
     
   - Three-way action execution pattern.  
   - Stage 1: `INVOKE_REQ` \$\\rightarrow\$ Stage 2: `INVOKE_ACK` (Action started) \$\\rightarrow\$ Stage 3: `INVOKE_RESP` (Action completed).

   

5. **Progress Pattern (SIP-5)**:  
     
   - Multi-stage pattern for long-running spacecraft tasks (e.g., flight software updates, orbit maneuvers).  
   - Stage 1: `PROGRESS_REQ` \$\\rightarrow\$ Stage 2: `PROGRESS_ACK` \$\\rightarrow\$ Stage 3...N: `PROGRESS_UPDATE` (Periodic telemetry updates) \$\\rightarrow\$ Final: `PROGRESS_RESP`.

   

6. **Publish/Subscribe Pattern (SIP-6)**:  
     
   - Broker-mediated loose coupling.  
   - `REGISTER` (Consumer subscribes to domain topic) \$\\rightarrow\$ `PUBLISH` (Provider publishes update) \$\\rightarrow\$ `NOTIFY` (Broker forwards to subscribers) \$\\rightarrow\$ `DEREGISTER`.

---

### 4\. MAL Message Header Specification

Every message exchanged across the MO framework carries a standard 16-field header:

- `uriFrom`: Uniform Resource Identifier of sender (e.g., `mal://moc.esa.esoc/fdir_client`).  
- `uriTo`: Uniform Resource Identifier of destination (e.g., `mal://spacecraft.artemis/power_service`).  
- `timestamp`: UTC ISO-8601 creation time epoch.  
- `qosLevel`: Quality of service (`BEST_EFFORT`, `QUEUED`, `TIMELY`, `ASSURED`).  
- `priority`: Numeric priority (1 to 10).  
- `domain`: Hierarchical domain identifier array (e.g. `['ARTEMIS', 'ORION', 'POWER']`).  
- `networkZone`: Network partition identifier (`SPACE_LINK` or `GROUND_LAN`).  
- `session`: Operational environment (`LIVE`, `SIMULATION`, `REPLAY`).  
- `sessionName`: Human-readable session identifier.  
- `interactionType`: Pattern code (1 to 6).  
- `interactionStage`: Exact pattern step name (e.g. `PROGRESS_UPDATE`).  
- `transactionId`: Unique 64-bit transaction identifier preserving correlation across stages.  
- `serviceArea`: SANA assigned Service Area identifier.  
- `serviceNumber`: Service code.  
- `operationNumber`: Operation code.  
- `areaVersion`: SANA Service Area version.  
- `isErrorMessage`: Boolean flag indicating whether payload carries an error structure.