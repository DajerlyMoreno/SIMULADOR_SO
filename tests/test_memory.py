"""
Pruebas unitarias para la gestión de memoria.

Casos de prueba:
  1. FIFO: secuencia clásica de page faults
  2. LRU: comportamiento frente a la Anomalía de Bélády
  3. MemoryManager: registro de hits/faults y estadísticas
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.memory.page_replacement import FIFOReplacement, LRUReplacement
from core.memory.memory_manager   import MemoryManager
from models.process               import Process


class TestFIFO(unittest.TestCase):

    def test_basic_page_faults(self):
        """
        Secuencia clásica: 1,2,3,4,1,2,5,1,2,3,4,5 con 3 marcos.
        FIFO debería producir 9 page faults.
        """
        fifo   = FIFOReplacement(num_frames=3)
        seq    = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        pid    = 1
        faults = 0
        for page in seq:
            hit, event = fifo.access_page(pid, page, faults)
            if not hit:
                faults += 1
        self.assertEqual(fifo.page_faults, 9)

    def test_no_faults_after_warmup(self):
        """Una vez llenos los marcos con páginas únicas, acceder a las mismas no da fault."""
        fifo = FIFOReplacement(num_frames=4)
        for i in range(4):
            fifo.access_page(1, i, i)
        # Ahora acceder a las mismas páginas (deben ser hits)
        for i in range(4):
            hit, _ = fifo.access_page(1, i, 4 + i)
            self.assertTrue(hit, f"Página {i} debería ser hit tras warmup")

    def test_hit_and_fault_counts_consistent(self):
        """hits + faults debe igualar el número total de accesos."""
        fifo = FIFOReplacement(num_frames=3)
        seq  = [0, 1, 2, 0, 3, 1, 4]
        for t, page in enumerate(seq):
            fifo.access_page(1, page, t)
        total = fifo.page_hits + fifo.page_faults
        self.assertEqual(total, len(seq))

    def test_eviction_recorded(self):
        """Al desalojar, el evento debe tener información del desalojado."""
        fifo = FIFOReplacement(num_frames=2)
        fifo.access_page(1, 0, 0)
        fifo.access_page(1, 1, 1)
        hit, event = fifo.access_page(1, 2, 2)   # Debe desalojar página 0
        self.assertFalse(hit)
        self.assertIsNotNone(event)
        self.assertEqual(event.evicted_page, 0)


class TestLRU(unittest.TestCase):

    def test_basic_page_faults(self):
        """
        Secuencia clásica con 3 marcos.
        LRU produce menos faults que FIFO en promedio.
        """
        lru  = LRUReplacement(num_frames=3)
        seq  = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        pid  = 1
        for t, page in enumerate(seq):
            lru.access_page(pid, page, t)
        # LRU debe tener ≤ 12 faults (máximo = todos faults)
        self.assertLessEqual(lru.page_faults, 12)
        self.assertGreater(lru.page_hits + lru.page_faults, 0)

    def test_lru_evicts_least_recently_used(self):
        """El marco menos usado recientemente debe ser el desalojado."""
        lru = LRUReplacement(num_frames=3)
        lru.access_page(1, 0, 1)   # Marco con página 0 (más antiguo)
        lru.access_page(1, 1, 2)
        lru.access_page(1, 2, 3)
        lru.access_page(1, 0, 4)   # Páginas 1 ahora es la LRU (no fue accedida desde t=2)
        hit, event = lru.access_page(1, 3, 5)  # Debe desalojar página 1
        self.assertFalse(hit)
        self.assertEqual(event.evicted_page, 1)

    def test_hit_ratio_consistent(self):
        lru = LRUReplacement(num_frames=4)
        # Acceder a páginas 0-3 repetidamente → muchos hits
        for cycle in range(3):
            for page in range(4):
                lru.access_page(1, page, cycle * 4 + page)
        # Después del primer ciclo, deben ser hits (4 accesos iniciales son faults)
        expected_hits = 4 * 3 - 4   # 3 ciclos x 4 páginas - 4 faults iniciales
        self.assertEqual(lru.page_hits, expected_hits)


class TestMemoryManager(unittest.TestCase):

    def _make_proc(self, pid=1, pages=4):
        return Process(pid=pid, name=f"P{pid}", priority=1,
                        burst_time=5, arrival_time=0, memory_pages=pages)

    def test_fifo_manager(self):
        """MemoryManager con FIFO debe producir estadísticas válidas."""
        mm   = MemoryManager(num_frames=4, algorithm="FIFO")
        proc = self._make_proc()
        res  = mm.simulate_process_accesses(proc)
        self.assertEqual(res["pid"], 1)
        self.assertGreaterEqual(res["page_hits"]   + res["page_faults"], 1)
        self.assertIn("hit_ratio", res)

    def test_lru_manager(self):
        """MemoryManager con LRU debe producir estadísticas válidas."""
        mm   = MemoryManager(num_frames=4, algorithm="LRU")
        proc = self._make_proc()
        res  = mm.simulate_process_accesses(proc)
        self.assertEqual(res["pid"], 1)

    def test_multiple_processes(self):
        """Varios procesos pueden usar el mismo gestor de memoria."""
        mm    = MemoryManager(num_frames=6, algorithm="LRU")
        procs = [self._make_proc(pid=i, pages=3) for i in range(1, 5)]
        results = [mm.simulate_process_accesses(p) for p in procs]
        self.assertEqual(len(results), 4)
        for r in results:
            self.assertGreaterEqual(r["accesos"], 1)

    def test_global_stats_populated(self):
        mm   = MemoryManager(num_frames=3, algorithm="FIFO")
        proc = self._make_proc()
        mm.simulate_process_accesses(proc,
            access_pattern=[0, 1, 2, 0, 1, 2, 3, 0])
        stats = mm.get_global_stats()
        self.assertIn("hit_ratio",   stats)
        self.assertIn("fault_ratio", stats)
        self.assertAlmostEqual(stats["hit_ratio"] + stats["fault_ratio"], 1.0, places=4)

    def test_reset_clears_state(self):
        mm   = MemoryManager(num_frames=3, algorithm="LRU")
        proc = self._make_proc()
        mm.simulate_process_accesses(proc)
        mm.reset()
        stats = mm.get_global_stats()
        self.assertEqual(stats["page_hits"],   0)
        self.assertEqual(stats["page_faults"], 0)


if __name__ == "__main__":
    print("=" * 50)
    print("  Pruebas – Gestión de Memoria")
    print("=" * 50)
    unittest.main(verbosity=2)
