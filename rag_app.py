"""
Resource Allocation Graph (RAG) - deadlock detection tool
21CSC202J - Operating Systems mini-project

Run:
    python rag_app.py            interactive menu
    python rag_app.py --demo     scripted demo (prints results and saves PNG pictures)

Naming convention: process nodes start with P (P1, P2, ...), resource nodes
start with R (R1, R2, ...). Every resource is a single-instance resource.
Drawing needs matplotlib (pip install matplotlib); everything else works
with plain Python 3.
"""
import sys


class ResourceAllocationGraph:
    def __init__(self):
        self.graph = {}

    def add_node(self, node):
        if node not in self.graph:
            self.graph[node] = []

    def add_edge(self, source, destination):
        self.add_node(source)
        self.add_node(destination)
        self.graph[source].append(destination)

    def print_graph(self):
        print("Resource Allocation Graph:")
        for node, neighbours in self.graph.items():
            print(f"{node} -> {', '.join(neighbours)}")

    def has_cycle(self):
        visited = set()
        active = set()

        def dfs(node):
            if node in active:
                return True
            if node in visited:
                return False

            visited.add(node)
            active.add(node)

            for neighbour in self.graph.get(node, []):
                if dfs(neighbour):
                    return True

            active.remove(node)
            return False

        for node in self.graph:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    # ------------------------------------------------------------------
    # Extensions added on top of the basic implementation
    # ------------------------------------------------------------------
    @staticmethod
    def is_process(node):
        return node[:1].upper() == "P"

    @staticmethod
    def is_resource(node):
        return node[:1].upper() == "R"

    def find_cycle(self):
        """Same DFS as has_cycle(), but returns the cycle as a list of nodes
        (first node repeated at the end), or None when there is no cycle."""
        visited = set()
        path = []          # nodes on the current DFS path, in order

        def dfs(node):
            if node in path:                       # back edge: node is active
                return path[path.index(node):] + [node]
            if node in visited:
                return None
            visited.add(node)
            path.append(node)
            for neighbour in self.graph.get(node, []):
                found = dfs(neighbour)
                if found:
                    return found
            path.pop()
            return None

        for node in list(self.graph):
            if node not in visited:
                found = dfs(node)
                if found:
                    return found
        return None

    def add_process(self, name):
        if not self.is_process(name):
            return "Process names must start with P (example: P1)."
        self.add_node(name)
        return f"Process {name} added."

    def add_resource(self, name):
        if not self.is_resource(name):
            return "Resource names must start with R (example: R1)."
        self.add_node(name)
        return f"Resource {name} added."

    def request(self, process, resource):
        """Request edge  P -> R."""
        if not (self.is_process(process) and self.is_resource(resource)):
            return "A request edge must go from a process (P..) to a resource (R..)."
        if resource in self.graph.get(process, []):
            return f"{process} already requests {resource}."
        if process in self.graph.get(resource, []):
            return f"{resource} is already allocated to {process}."
        self.add_edge(process, resource)
        return f"Request edge added: {process} -> {resource}"

    def allocate(self, resource, process):
        """Assignment edge  R -> P  (a single-instance resource has one holder)."""
        if not (self.is_resource(resource) and self.is_process(process)):
            return "An assignment edge must go from a resource (R..) to a process (P..)."
        if self.graph.get(resource):
            return f"{resource} is already allocated to {self.graph[resource][0]}."
        self.add_edge(resource, process)
        if resource in self.graph.get(process, []):      # request is now granted
            self.graph[process].remove(resource)
        return f"Assignment edge added: {resource} -> {process}"

    def release(self, resource, process):
        if process in self.graph.get(resource, []):
            self.graph[resource].remove(process)
            return f"{process} released {resource}."
        return f"{resource} is not allocated to {process}."

    def report(self):
        cycle = self.find_cycle()
        if cycle:
            print("Cycle detected: possible deadlock")
            print("Deadlock cycle: " + " -> ".join(cycle))
            procs = sorted({n for n in cycle if self.is_process(n)})
            print("Deadlocked processes: " + ", ".join(procs))
        else:
            print("No cycle detected: no deadlock in this model")
        return cycle

    # ------------------------------------------------------------------
    # Drawing (needs matplotlib)
    # ------------------------------------------------------------------
    def draw(self, filename="rag_graph.png", show=True):
        try:
            import matplotlib
            if not show:
                matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.patches import Circle, Rectangle, FancyArrowPatch
        except ImportError:
            print("matplotlib is not installed. Run: pip install matplotlib")
            return
        if not self.graph:
            print("The graph is empty - nothing to draw.")
            return

        procs = sorted(n for n in self.graph if self.is_process(n))
        ress = sorted(n for n in self.graph if self.is_resource(n))
        gap = 3.0                                   # horizontal distance between nodes
        width = gap * (max(len(procs), len(ress), 1) - 1)
        pos = {}
        for row, y in ((procs, 3.6), (ress, 0.0)):
            start = (width - gap * (len(row) - 1)) / 2
            for i, node in enumerate(row):
                pos[node] = (start + i * gap, y)

        cycle = self.find_cycle()
        cycle_edges = set(zip(cycle, cycle[1:])) if cycle else set()

        fig, ax = plt.subplots(figsize=(max(6.5, 1.5 * (width + 3)), 5.2))
        ax.set_xlim(-1.5, width + 1.5)
        ax.set_ylim(-1.3, 4.7)
        ax.set_aspect("equal")
        ax.axis("off")
        radius = 0.42

        for src, targets in self.graph.items():
            for dst in targets:
                (x1, y1), (x2, y2) = pos[src], pos[dst]
                in_cycle = (src, dst) in cycle_edges
                arrow = FancyArrowPatch(
                    (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                    lw=3 if in_cycle else 1.6,
                    color="#c62828" if in_cycle else "#333333",
                    connectionstyle="arc3,rad=0.12",
                    shrinkA=radius * 48, shrinkB=radius * 48, zorder=1)
                ax.add_patch(arrow)

        for node, (x, y) in pos.items():
            if self.is_process(node):
                ax.add_patch(Circle((x, y), radius, fc="#dbe9f7", ec="#222", lw=2, zorder=3))
                ax.text(x, y, node, ha="center", va="center", fontsize=14, weight="bold", zorder=4)
            else:
                ax.add_patch(Rectangle((x - radius, y - radius), 2 * radius, 2 * radius,
                                       fc="#fde9c8", ec="#222", lw=2, zorder=3))
                ax.text(x, y + 0.1, node, ha="center", va="center", fontsize=14, weight="bold", zorder=4)
                ax.add_patch(Circle((x, y - 0.2), 0.06, fc="k", zorder=5))

        if cycle:
            title = "DEADLOCK: " + " → ".join(cycle)
            color = "#c62828"
        else:
            title = "No cycle: no deadlock"
            color = "#2e7d32"
        ax.text(width / 2, 4.5, title, ha="center", fontsize=14, weight="bold", color=color)
        ax.text(width / 2, -1.1, "circle = process     square = resource     "
                "P → R request     R → P assignment",
                ha="center", fontsize=10, color="#555")
        fig.savefig(filename, dpi=160, bbox_inches="tight", facecolor="white")
        print(f"Picture saved as {filename}")
        if show:
            plt.show()
        plt.close(fig)


# ----------------------------------------------------------------------
# Ready-made examples
# ----------------------------------------------------------------------
def load_deadlock_example():
    g = ResourceAllocationGraph()
    g.allocate("R1", "P1")
    g.request("P1", "R2")
    g.allocate("R2", "P2")
    g.request("P2", "R1")
    return g


def load_safe_example():
    g = ResourceAllocationGraph()
    g.allocate("R1", "P1")
    g.request("P2", "R1")
    return g


# ----------------------------------------------------------------------
# Interactive menu
# ----------------------------------------------------------------------
MENU = """
==== Resource Allocation Graph ====
 1. Add process            6. Show graph (text)
 2. Add resource           7. Check for deadlock
 3. Request  (P -> R)      8. Draw graph
 4. Allocate (R -> P)      9. Load deadlock example
 5. Release  (R, P)       10. Load safe example
                           0. Exit
"""


def interactive():
    g = ResourceAllocationGraph()
    while True:
        print(MENU)
        try:
            choice = input("Choose an option: ").strip()
            if choice == "1":
                print(g.add_process(input("Process name (e.g. P1): ").strip().upper()))
            elif choice == "2":
                print(g.add_resource(input("Resource name (e.g. R1): ").strip().upper()))
            elif choice == "3":
                p = input("Process: ").strip().upper()
                r = input("Resource it requests: ").strip().upper()
                print(g.request(p, r))
            elif choice == "4":
                r = input("Resource: ").strip().upper()
                p = input("Process it is allocated to: ").strip().upper()
                print(g.allocate(r, p))
            elif choice == "5":
                r = input("Resource: ").strip().upper()
                p = input("Process releasing it: ").strip().upper()
                print(g.release(r, p))
            elif choice == "6":
                g.print_graph()
            elif choice == "7":
                g.report()
            elif choice == "8":
                g.draw()
            elif choice == "9":
                g = load_deadlock_example()
                print("Deadlock example loaded.")
                g.print_graph()
            elif choice == "10":
                g = load_safe_example()
                print("Safe example loaded.")
                g.print_graph()
            elif choice == "0":
                print("Goodbye.")
                return
            else:
                print("Please choose a number from the menu.")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return


def demo():
    print("=== 1. Deadlock-prone allocation ===")
    g = load_deadlock_example()
    g.print_graph()
    g.report()
    g.draw("demo_deadlock.png", show=False)

    print("\n=== 2. Safe allocation ===")
    g = load_safe_example()
    g.print_graph()
    g.report()
    g.draw("demo_safe.png", show=False)

    print("\n=== 3. Deadlock appears, then is resolved ===")
    g = load_safe_example()
    print(g.request("P1", "R2"))
    print(g.allocate("R2", "P2"))
    g.report()
    g.draw("demo_deadlock_formed.png", show=False)
    print("Recovery: P1 is terminated, so it releases R1 and drops its request for R2:")
    print(g.release("R1", "P1"))
    g.graph["P1"] = []
    g.report()


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        interactive()
