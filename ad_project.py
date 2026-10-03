import sys
import time


class Entry:
    def __init__(self, key, value, value_type):
        self.key = key
        self.value = value
        self.value_type = value_type
        self.expire_at = -1
        self.next = None


class HashTable:
    def __init__(self, capacity=1024):
        self.capacity = capacity
        self.buckets = [None] * capacity

    def _hash(self, key):
        h = 0
        p = 131
        for ch in key:
            h = (h * p + ord(ch)) % self.capacity
        return h

    def get_entry(self, key):
        idx = self._hash(key)
        cur = self.buckets[idx]
        while cur is not None:
            if cur.key == key:
                return cur
            cur = cur.next
        return None

    def set_entry(self, key, value, value_type):
        idx = self._hash(key)
        cur = self.buckets[idx]
        while cur is not None:
            if cur.key == key:
                cur.value = value
                cur.value_type = value_type
                return cur
            cur = cur.next

        new_node = Entry(key, value, value_type)
        new_node.next = self.buckets[idx]
        self.buckets[idx] = new_node
        return new_node

    def delete(self, key):
        idx = self._hash(key)
        cur = self.buckets[idx]
        prev = None
        while cur is not None:
            if cur.key == key:
                if prev is None:
                    self.buckets[idx] = cur.next
                else:
                    prev.next = cur.next
                return True
            prev = cur
            cur = cur.next
        return False


class ListNode:
    def __init__(self, value):
        self.value = value
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def lpush(self, value):
        node = ListNode(value)
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node
        self.length += 1

    def rpush(self, value):
        node = ListNode(value)
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self.length += 1

    def lpop(self):
        if self.head is None:
            return None
        val = self.head.value
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        else:
            self.head.prev = None
        self.length -= 1
        return val

    def rpop(self):
        if self.tail is None:
            return None
        val = self.tail.value
        self.tail = self.tail.prev
        if self.tail is None:
            self.head = None
        else:
            self.tail.next = None
        self.length -= 1
        return val

    def lrange(self, start, end):
        if start < 0:
            start = 0
        if end < 0 or start > end:
            return []

        result = []
        idx = 0
        cur = self.head
        while cur is not None:
            if start <= idx <= end:
                result.append(cur.value)
            if idx > end:
                break
            idx += 1
            cur = cur.next
        return result


class ZNode:
    def __init__(self, member, score):
        self.member = member
        self.score = score
        self.next = None


class SortedSet:
    def __init__(self):
        self.head = None

    def _find_member(self, member):
        cur = self.head
        prev = None
        while cur is not None:
            if cur.member == member:
                return prev, cur
            prev = cur
            cur = cur.next
        return None, None

    def zadd(self, score, member):
        prev, cur = self._find_member(member)
        found = False
        if cur is not None:
            found = True
            if prev is None:
                self.head = cur.next
            else:
                prev.next = cur.next

        new_node = ZNode(member, score)
        cur = self.head
        prev = None
        while cur is not None and cur.score <= score:
            prev = cur
            cur = cur.next

        if prev is None:
            new_node.next = self.head
            self.head = new_node
        else:
            new_node.next = cur
            prev.next = new_node

        return 0 if found else 1

    def zrem(self, member):
        prev, cur = self._find_member(member)
        if cur is None:
            return 0
        if prev is None:
            self.head = cur.next
        else:
            prev.next = cur.next
        return 1

    def zscore(self, member):
        _, cur = self._find_member(member)
        if cur is None:
            return None
        return cur.score

    def zrank(self, member):
        idx = 0
        cur = self.head
        while cur is not None:
            if cur.member == member:
                return idx
            idx += 1
            cur = cur.next
        return None


class Graph:
    def __init__(self):
        self.nodes = set()
        self.adj = {}

    def add_node(self, node):
        if node in self.nodes:
            return
        self.nodes.add(node)
        self.adj[node] = []

    def add_edge(self, u, v, w):
        if u not in self.nodes:
            self.add_node(u)
        if v not in self.nodes:
            self.add_node(v)
        self.adj[u].append((v, w))
        self.adj[v].append((u, w))

    def connected(self, start, target):
        if start not in self.nodes or target not in self.nodes:
            return False
        visited = set()
        stack = [start]
        while stack:
            u = stack.pop()
            if u == target:
                return True
            if u in visited:
                continue
            visited.add(u)
            for v, _w in self.adj.get(u, []):
                if v not in visited:
                    stack.append(v)
        return False

    def mst_weight(self):
        if not self.nodes:
            return 0
        visited = set()
        total = 0

        start = next(iter(self.nodes))
        visited.add(start)

        edges = []
        for v, w in self.adj[start]:
            edges.append((w, start, v))

        while edges:
            edges.sort(key=lambda x: x[0])
            w, u, v = edges.pop(0)
            if v in visited:
                continue
            visited.add(v)
            total += w
            for x, wx in self.adj[v]:
                if x not in visited:
                    edges.append((wx, v, x))

        return total


class RedisLite:
    def __init__(self):
        self.table = HashTable()

    def _expired(self, entry):
        if entry is None:
            return True
        if entry.expire_at == -1:
            return False
        now = int(time.time())
        if now >= entry.expire_at:
            self.table.delete(entry.key)
            return True
        return False

    def set_cmd(self, key, value):
        entry = self.table.set_entry(key, value, "string")
        entry.expire_at = -1
        print("OK")

    def get_cmd(self, key):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print("NULL")
            return
        if entry.value_type != "string":
            print("WRONGTYPE")
            return
        print(entry.value)

    def del_cmd(self, key):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print(0)
            return
        ok = self.table.delete(key)
        if ok:
            print(1)
        else:
            print(0)

    def exists_cmd(self, key):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print(0)
            return
        print(1)

    def expire_cmd(self, key, seconds):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print(0)
            return
        entry.expire_at = int(time.time()) + seconds
        print(1)

    def ttl_cmd(self, key):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print(-2)
            return
        if entry.expire_at == -1:
            print(-1)
            return
        now = int(time.time())
        remaining = entry.expire_at - now
        if remaining < 0:
            self.table.delete(key)
            print(-2)
        else:
            print(remaining)

    def lpush_cmd(self, key, value):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            lst = DoublyLinkedList()
            lst.lpush(value)
            self.table.set_entry(key, lst, "list")
            print(1)
            return
        if entry.value_type != "list":
            print("WRONGTYPE")
            return
        entry.value.lpush(value)
        print(entry.value.length)

    def rpush_cmd(self, key, value):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            lst = DoublyLinkedList()
            lst.rpush(value)
            self.table.set_entry(key, lst, "list")
            print(1)
            return
        if entry.value_type != "list":
            print("WRONGTYPE")
            return
        entry.value.rpush(value)
        print(entry.value.length)

    def lpop_cmd(self, key):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print("NULL")
            return
        if entry.value_type != "list":
            print("WRONGTYPE")
            return
        val = entry.value.lpop()
        if val is None:
            print("NULL")
        else:
            print(val)

    def rpop_cmd(self, key):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print("NULL")
            return
        if entry.value_type != "list":
            print("WRONGTYPE")
            return
        val = entry.value.rpop()
        if val is None:
            print("NULL")
        else:
            print(val)

    def lrange_cmd(self, key, start, end):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print("NULL")
            return
        if entry.value_type != "list":
            print("WRONGTYPE")
            return
        items = entry.value.lrange(start, end)
        if not items:
            print("NULL")
        else:
            print(" ".join(items))

    def zadd_cmd(self, key, score, member):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            zset = SortedSet()
            result = zset.zadd(score, member)
            self.table.set_entry(key, zset, "zset")
            print(result)
            return
        if entry.value_type != "zset":
            print("WRONGTYPE")
            return
        res = entry.value.zadd(score, member)
        print(res)

    def zrem_cmd(self, key, member):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print(0)
            return
        if entry.value_type != "zset":
            print("WRONGTYPE")
            return
        res = entry.value.zrem(member)
        print(res)

    def zscore_cmd(self, key, member):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print("NULL")
            return
        if entry.value_type != "zset":
            print("WRONGTYPE")
            return
        s = entry.value.zscore(member)
        if s is None:
            print("NULL")
        else:
            print(s)

    def zrank_cmd(self, key, member):
        entry = self.table.get_entry(key)
        if entry is None or self._expired(entry):
            print("NULL")
            return
        if entry.value_type != "zset":
            print("WRONGTYPE")
            return
        r = entry.value.zrank(member)
        if r is None:
            print("NULL")
        else:
            print(r)

    def gcreate_cmd(self, gname):
        entry = self.table.get_entry(gname)
        if entry is not None and not self._expired(entry):
            if entry.value_type != "graph":
                print("WRONGTYPE")
                return
            print("OK")
            return
        g = Graph()
        self.table.set_entry(gname, g, "graph")
        print("OK")

    def gaddnode_cmd(self, gname, node):
        entry = self.table.get_entry(gname)
        if entry is None or self._expired(entry):
            print("ERROR")
            return
        if entry.value_type != "graph":
            print("WRONGTYPE")
            return
        entry.value.add_node(node)
        print("OK")

    def gaddedge_cmd(self, gname, u, v, weight):
        entry = self.table.get_entry(gname)
        if entry is None or self._expired(entry):
            print("ERROR")
            return
        if entry.value_type != "graph":
            print("WRONGTYPE")
            return
        entry.value.add_edge(u, v, weight)
        print("OK")

    def gconnected_cmd(self, gname, u, v):
        entry = self.table.get_entry(gname)
        if entry is None or self._expired(entry):
            print(0)
            return
        if entry.value_type != "graph":
            print("WRONGTYPE")
            return
        ok = entry.value.connected(u, v)
        if ok:
            print(1)
        else:
            print(0)

    def gmst_cmd(self, gname):
        entry = self.table.get_entry(gname)
        if entry is None or self._expired(entry):
            print("NULL")
            return
        if entry.value_type != "graph":
            print("WRONGTYPE")
            return
        w = entry.value.mst_weight()
        print(w)

    def execute(self, line):
        line = line.strip()
        if line == "":
            return

        parts = line.split()
        cmd = parts[0]

        if cmd == "SET":
            if len(parts) < 3:
                print("ERROR")
                return
            key = parts[1]
            value = " ".join(parts[2:])
            self.set_cmd(key, value)

        elif cmd == "GET":
            if len(parts) != 2:
                print("ERROR")
                return
            self.get_cmd(parts[1])

        elif cmd == "DEL":
            if len(parts) != 2:
                print("ERROR")
                return
            self.del_cmd(parts[1])

        elif cmd == "EXISTS":
            if len(parts) != 2:
                print("ERROR")
                return
            self.exists_cmd(parts[1])

        elif cmd == "EXPIRE":
            if len(parts) != 3:
                print("ERROR")
                return
            key = parts[1]
            try:
                sec = int(parts[2])
            except ValueError:
                print("ERROR")
                return
            self.expire_cmd(key, sec)

        elif cmd == "TTL":
            if len(parts) != 2:
                print("ERROR")
                return
            self.ttl_cmd(parts[1])

        elif cmd == "LPUSH":
            if len(parts) < 3:
                print("ERROR")
                return
            key = parts[1]
            value = " ".join(parts[2:])
            self.lpush_cmd(key, value)

        elif cmd == "RPUSH":
            if len(parts) < 3:
                print("ERROR")
                return
            key = parts[1]
            value = " ".join(parts[2:])
            self.rpush_cmd(key, value)

        elif cmd == "LPOP":
            if len(parts) != 2:
                print("ERROR")
                return
            self.lpop_cmd(parts[1])

        elif cmd == "RPOP":
            if len(parts) != 2:
                print("ERROR")
                return
            self.rpop_cmd(parts[1])

        elif cmd == "LRANGE":
            if len(parts) != 4:
                print("ERROR")
                return
            key = parts[1]
            try:
                start = int(parts[2])
                end = int(parts[3])
            except ValueError:
                print("ERROR")
                return
            self.lrange_cmd(key, start, end)

        elif cmd == "ZADD":
            if len(parts) < 4:
                print("ERROR")
                return
            key = parts[1]
            try:
                score = float(parts[2])
            except ValueError:
                print("ERROR")
                return
            member = " ".join(parts[3:])
            self.zadd_cmd(key, score, member)

        elif cmd == "ZREM":
            if len(parts) < 3:
                print("ERROR")
                return
            key = parts[1]
            member = " ".join(parts[2:])
            self.zrem_cmd(key, member)

        elif cmd == "ZSCORE":
            if len(parts) < 3:
                print("ERROR")
                return
            key = parts[1]
            member = " ".join(parts[2:])
            self.zscore_cmd(key, member)

        elif cmd == "ZRANK":
            if len(parts) < 3:
                print("ERROR")
                return
            key = parts[1]
            member = " ".join(parts[2:])
            self.zrank_cmd(key, member)

        elif cmd == "GCREATE":
            if len(parts) != 2:
                print("ERROR")
                return
            self.gcreate_cmd(parts[1])

        elif cmd == "GADDNODE":
            if len(parts) != 3:
                print("ERROR")
                return
            self.gaddnode_cmd(parts[1], parts[2])

        elif cmd == "GADDEDGE":
            if len(parts) != 5:
                print("ERROR")
                return
            gname = parts[1]
            u = parts[2]
            v = parts[3]
            try:
                w = float(parts[4])
            except ValueError:
                print("ERROR")
                return
            self.gaddedge_cmd(gname, u, v, w)

        elif cmd == "GCONNECTED":
            if len(parts) != 4:
                print("ERROR")
                return
            self.gconnected_cmd(parts[1], parts[2], parts[3])

        elif cmd == "GMST":
            if len(parts) != 2:
                print("ERROR")
                return
            self.gmst_cmd(parts[1])

        else:
            print("ERROR")


def main():
    db = RedisLite()
    for line in sys.stdin:
        db.execute(line)


if __name__ == "__main__":
    main()
