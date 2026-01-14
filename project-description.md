# **Technical Specification: Arena to Cin7 Data Synchronization**

## **1\. Integration Overview**

The goal of this service is to automate the transfer of Item and Bill of Material (BOM) data from Arena PLM to Cin7 Omni. The synchronization ensures that product data remains consistent between engineering (Arena) and operations/inventory (Cin7).

## **2\. Sync Trigger Mechanism**

The synchronization should be event-driven.

- **Trigger Event:** An Arena Change Object reaches the Lifecycle Status of **"Completed"**.
- **Action:** Immediately initiate the sync for all items associated with that Change Object that meet the filter criteria.

## **3\. Pre-Sync Filtering Rules**

Before data is pushed to Cin7, the connector must evaluate the following:

- **Global Sync Filter:** Only items where the Arena field "Transfer Data to ERP?" is set to **"Yes"** should be included in the sync.
- **BOM Exception:** If a Parent Item is being synced but one of its Child Items (components) has "Transfer Data to ERP?" set to **"No"**, the connector must **exclude only that Child Item** from the BOM data transmitted to Cin7, while still syncing the rest of the BOM and the Parent Item itself.

## **4\. Field Mapping & Data Transformation**

### **4.1. Core Product Mapping**

| Arena Item Field Name                   | Cin7 Product Field Name | Transformation / Logic                                               |
| :-------------------------------------- | :---------------------- | :------------------------------------------------------------------- |
| item_number                             | ProductCode             | Primary Identifier                                                   |
| item_name                               | Name                    |                                                                      |
| revision                                | AdditionalAttribute1    |                                                                      |
| item category                           | Category                |                                                                      |
| description                             | Description             |                                                                      |
| unit of measure                         | DefaultUnitOfMeasure    |                                                                      |
| Costing Method                          | CostingMethod           |                                                                      |
| Auto Assemble                           | AutoAssemble            |                                                                      |
| Inventory Account                       | InventoryAccount        |                                                                      |
| COGS Account                            | COGSAccount             |                                                                      |
| Sellable                                | Sellable                |                                                                      |
| Internal Note for ERP                   | InternalNote            |                                                                      |
| Last GLG CO                             | AdditionalAttribute2    |                                                                      |
| manufacturer & manufacturer_item_number | AdditionalAttribute4    | **Combined String:** "\[manufacturer\] \[manufacturer_item_number\]" |

### **4.2. BOM (Bill of Materials) Mapping**

Used when populating product components.  
| Arena Field Name | Cin7 Field Name |  
| :--- | :--- |  
| Parent Item Number | ProductSKU |  
| Child Item Number | ComponentSKU |  
| Quantity | Quantity |

## **5\. System Default Values**

The following Cin7 fields should be populated with hardcoded defaults during the sync process:

- **Revenue Account:** Set to 4001: OEM Product.
- **Default Location:** Set to Main Warehouse.
- **Product Type:** Set to Stock.

## **6\. Business Logic for BOMs**

The connector must handle BOM creation and updates based on the following logic:

1. **For Existing Products in Cin7:**
   - If the product exists but has no BOM, and the Arena Item **has** a BOM:
     - Set AssemblyBOM \= Yes.
     - Populate the BOM components.
   - Otherwise, if no BOM exists in Arena, set AssemblyBOM \= No.
2. **For New Products (not yet in Cin7):**
   - If the new Arena Item has a BOM:
     - Set AssemblyBOM \= Yes.
     - Populate the BOM components.
   - If the new Arena Item has no BOM:
     - Set AssemblyBOM \= No.

## **7\. Implementation Notes**

- **Manufacturer String:** Ensure a space exists between the manufacturer name and the part number in AdditionalAttribute4.
- **API Errors:** Implement logging for items that fail the sync (e.g., missing mandatory fields in Cin7 or invalid category names).
- **Update Logic:** If an item already exists in Cin7, the service should update the existing record based on the ProductCode.
