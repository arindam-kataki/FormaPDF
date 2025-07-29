import time
from typing import List, Set, Optional, Tuple
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QBrush, QPen
from PyQt6.QtCore import Qt

class SmartScrollOptimizer:
    """
    Optimizes canvas repainting during scrolling by detecting scroll direction
    and only repainting pages that actually need updates.
    """

    def __init__(self, canvas_widget):
        self.canvas_widget = canvas_widget
        self.last_visible_pages: List[int] = []
        self.last_viewport_rect = QRectF()
        self.last_scroll_time = 0.0
        self.scroll_direction = None
        self.scroll_velocity = 0.0

        # Performance tracking
        self.total_scrolls = 0
        self.repaints_saved = 0

        print("🚀 SmartScrollOptimizer initialized")

    def update_visible_pages_optimized(self, new_visible_pages: List[int], new_viewport_rect: QRectF):
        """
        Main optimization method - determines what actually needs repainting
        """
        current_time = time.time()

        # Detect scroll characteristics
        scroll_info = self._analyze_scroll_movement(new_viewport_rect, current_time)

        # Calculate optimal repaint strategy
        pages_to_repaint, pages_to_skip = self._calculate_repaint_strategy(
            self.last_visible_pages,
            new_visible_pages,
            scroll_info
        )

        # Log optimization results
        self._log_optimization_results(
            self.last_visible_pages,
            new_visible_pages,
            pages_to_repaint,
            pages_to_skip,
            scroll_info
        )

        # Update canvas state
        self.canvas_widget.visible_pages = new_visible_pages
        self.canvas_widget.viewport_rect = new_viewport_rect

        # Execute optimized repaint
        if pages_to_repaint:
            self.canvas_widget._smart_repaint_pages(pages_to_repaint, pages_to_skip)
        else:
            print("🎨 SUPER OPTIMIZATION: No repaint needed at all!")

        # Update tracking state
        self._update_tracking_state(new_visible_pages, new_viewport_rect, current_time)

    def _analyze_scroll_movement(self, new_viewport_rect: QRectF, current_time: float) -> dict:
        """Analyze scroll direction, speed, and type"""

        if not self.last_viewport_rect.isValid():
            return {
                'direction': 'initial',
                'velocity': 0.0,
                'dx': 0.0,
                'dy': 0.0,
                'time_delta': 0.0
            }

        # Calculate movement
        dx = new_viewport_rect.x() - self.last_viewport_rect.x()
        dy = new_viewport_rect.y() - self.last_viewport_rect.y()
        time_delta = current_time - self.last_scroll_time

        # Calculate velocity
        distance = (dx ** 2 + dy ** 2) ** 0.5
        velocity = distance / time_delta if time_delta > 0 else 0.0

        # Determine scroll direction
        direction = self._classify_scroll_direction(dx, dy)

        return {
            'direction': direction,
            'velocity': velocity,
            'dx': dx,
            'dy': dy,
            'time_delta': time_delta
        }

    def _classify_scroll_direction(self, dx: float, dy: float) -> str:
        """Classify scroll direction with intelligent thresholds"""

        # Dynamic thresholds based on viewport size
        h_threshold = 10  # Horizontal movement threshold
        v_threshold = 10  # Vertical movement threshold

        moved_h = abs(dx) > h_threshold
        moved_v = abs(dy) > v_threshold

        if moved_v and moved_h:
            # Diagonal movement - check which is dominant
            if abs(dy) > abs(dx) * 2:
                return 'vertical_dominant'
            elif abs(dx) > abs(dy) * 2:
                return 'horizontal_dominant'
            else:
                return 'diagonal'
        elif moved_v:
            return 'vertical'
        elif moved_h:
            return 'horizontal'
        else:
            return 'minimal'

    def _calculate_repaint_strategy(self, old_pages: List[int], new_pages: List[int], scroll_info: dict) -> Tuple[
        Set[int], Set[int]]:
        """Calculate which pages to repaint vs which to keep cached"""

        old_set = set(old_pages)
        new_set = set(new_pages)
        direction = scroll_info['direction']

        if direction in ['vertical', 'vertical_dominant']:
            # MAJOR OPTIMIZATION: Vertical scrolling
            pages_to_repaint = new_set - old_set  # Only new pages
            pages_to_skip = old_set & new_set  # Pages still visible

        elif direction in ['horizontal', 'horizontal_dominant']:
            # Horizontal scrolling: Content within pages shifts
            pages_to_repaint = new_set
            pages_to_skip = set()

        elif direction == 'diagonal':
            # Conservative approach for diagonal
            pages_to_repaint = new_set
            pages_to_skip = set()

        elif direction == 'minimal':
            # Tiny movements: Smart detection
            if old_set == new_set:
                pages_to_repaint = set()  # No page changes
                pages_to_skip = new_set
            else:
                pages_to_repaint = new_set - old_set  # Only new pages
                pages_to_skip = old_set & new_set

        else:  # 'initial' or unknown
            pages_to_repaint = new_set
            pages_to_skip = set()

        return pages_to_repaint, pages_to_skip

    def _log_optimization_results(self, old_pages: List[int], new_pages: List[int],
                                  pages_to_repaint: Set[int], pages_to_skip: Set[int],
                                  scroll_info: dict):
        """Log optimization performance"""

        direction = scroll_info['direction']
        velocity = scroll_info['velocity']

        total_pages = len(new_pages)
        repaint_pages = len(pages_to_repaint)
        skip_pages = len(pages_to_skip)

        if total_pages > 0:
            efficiency = (skip_pages / total_pages) * 100
        else:
            efficiency = 0

        # Update statistics
        self.total_scrolls += 1
        self.repaints_saved += skip_pages

        print(f"📜 SMART SCROLL #{self.total_scrolls}:")
        print(f"   Direction: {direction} (velocity: {velocity:.1f})")
        print(f"   Pages: {old_pages} → {new_pages}")
        print(f"   Strategy: Repaint {repaint_pages}, Skip {skip_pages} ({efficiency:.1f}% cached)")

        if skip_pages > 0:
            print(f"   🚀 SAVED {skip_pages} repaints! (Total saved: {self.repaints_saved})")

    def _update_tracking_state(self, new_visible_pages: List[int], new_viewport_rect: QRectF, current_time: float):
        """Update internal tracking state"""
        self.last_visible_pages = new_visible_pages.copy()
        self.last_viewport_rect = new_viewport_rect
        self.last_scroll_time = current_time

    def get_performance_stats(self) -> dict:
        """Get optimization performance statistics"""
        return {
            'total_scrolls': self.total_scrolls,
            'repaints_saved': self.repaints_saved,
            'efficiency': (self.repaints_saved / max(self.total_scrolls, 1)) * 100
        }