"""
Fix hierarchy metadata: Mark CRB, ETF Amber, MSET as leaf nodes
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("FIXING HIERARCHY METADATA: Marking CRB, ETF Amber, MSET as Leaf Nodes")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Step 1: Verify nodes exist and current state
        print("Step 1: Verifying nodes exist and checking current state...")
        result = conn.execute(text("""
            SELECT node_id, node_name, is_leaf, parent_node_id
            FROM dim_hierarchy
            WHERE node_name IN ('CRB', 'ETF Amber', 'MSET')
            ORDER BY node_name
        """))
        
        nodes = result.fetchall()
        if not nodes:
            print("[ERROR] No nodes found with names 'CRB', 'ETF Amber', 'MSET'")
            return 1
        
        print(f"[OK] Found {len(nodes)} node(s):")
        nodes_to_update = []
        for node in nodes:
            node_id, node_name, is_leaf, parent_id = node
            print(f"   {node_id} ('{node_name}'): is_leaf={is_leaf}, parent={parent_id}")
            if not is_leaf:
                nodes_to_update.append((node_id, node_name))
        
        if not nodes_to_update:
            print()
            print("[INFO] All nodes are already marked as leaf nodes - no update needed")
            return 0
        
        print()
        print(f"[UPDATE REQUIRED] {len(nodes_to_update)} node(s) need to be updated:")
        for node_id, node_name in nodes_to_update:
            print(f"   {node_id} ('{node_name}')")
        print()
        
        # Step 2: Verify nodes have no children (safety check)
        print("Step 2: Verifying nodes have no children (safety check)...")
        for node_id, node_name in nodes_to_update:
            result = conn.execute(text("""
                SELECT COUNT(*) as child_count
                FROM dim_hierarchy
                WHERE parent_node_id = :node_id
            """), {"node_id": node_id})
            
            child_count = result.fetchone()[0]
            if child_count > 0:
                print(f"[WARNING] {node_name} ({node_id}) has {child_count} children!")
                print(f"   This node should NOT be marked as leaf - aborting update")
                return 1
            else:
                print(f"[OK] {node_name} ({node_id}) has no children - safe to mark as leaf")
        
        print()
        
        # Step 3: Execute the update
        print("Step 3: Executing UPDATE...")
        print("   SQL: UPDATE dim_hierarchy SET is_leaf = true WHERE node_name IN ('CRB', 'ETF Amber', 'MSET')")
        print()
        
        try:
            result = conn.execute(text("""
                UPDATE dim_hierarchy
                SET is_leaf = true
                WHERE node_name IN ('CRB', 'ETF Amber', 'MSET')
                  AND is_leaf = false
            """))
            
            rows_affected = result.rowcount
            conn.commit()
            
            print(f"[SUCCESS] Update executed - {rows_affected} row(s) affected")
            print()
            
            # Step 4: Verify the update
            print("Step 4: Verifying update...")
            result = conn.execute(text("""
                SELECT node_id, node_name, is_leaf, parent_node_id
                FROM dim_hierarchy
                WHERE node_name IN ('CRB', 'ETF Amber', 'MSET')
                ORDER BY node_name
            """))
            
            updated_nodes = result.fetchall()
            print(f"[VERIFIED] Updated nodes:")
            all_correct = True
            for node in updated_nodes:
                node_id, node_name, is_leaf, parent_id = node
                status = "[OK]" if is_leaf else "[ERROR]"
                print(f"   {status} {node_id} ('{node_name}'): is_leaf={is_leaf}, parent={parent_id}")
                if not is_leaf:
                    all_correct = False
            
            if all_correct:
                print()
                print("[SUCCESS] All nodes are now correctly marked as leaf nodes!")
                print()
                print("Next Steps:")
                print("   1. Re-run calculation for Use Case 3")
                print("   2. Verify Adjusted P&L values are now populated (not zero)")
                print("   3. Check that waterfall_up() no longer overwrites these values")
            else:
                print()
                print("[WARNING] Some nodes are still not marked as leaf - check manually")
            
            return 0
            
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Update failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    exit(main())

