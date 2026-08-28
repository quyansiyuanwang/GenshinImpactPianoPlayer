"""Score file and application lifecycle commands."""

from __future__ import annotations

from src.application.state.state_machine import PlayerState as PSM_State
from src.core.keyboard.controller import KeyboardController
from src.core.parser.score_parser import ScoreParser
from src.core.player.player import Player
from src.application.host_protocol import ApplicationHost

class FileActionsMixin(ApplicationHost):
    """Application command methods."""

    def quit(self) -> None:
        """Quit the application."""
        # Cleanup plugins
        from src.plugins.core.loader import cleanup_plugins
    
        cleanup_plugins()
    
        # Stop player
        if self.player:
            self.player.stop()
    
        self.running = False
    
    
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        if not self.player or not self.original_content:
            return
    
        try:
            # Get current configuration values (rounded so float dust from
            # repeated hotkey adjustments never reaches the score file)
            speed_multiplier = round(self.player._speed_multiplier, 6)
            arpeggio_interval = round(self.player._arpeggio_interval, 6)
            arpeggio_auto = self.player.get_arpeggio_auto()
            interval_rating = round(self.player._interval_rating, 6)
            line_interval_rating = round(self.player._line_interval_rating, 6)
            space_interval_rating = round(self.player._space_interval_rating, 6)
            empty_line_interval_rating = round(
                self.player._empty_line_interval_rating, 6
            )
            segment_length = self.player._segment_length
            segment_strict = self.player.get_segment_strict()
            loop = self.player.get_loop_enabled()
    
            # Parse the original content
            lines = self.original_content.split("\n")
            new_lines = []
            config_section = True
            config_updated = {
                "speed_multiplier": False,
                "arpeggio_interval": False,
                "arpeggio_auto": False,
                "interval_rating": False,
                "line_interval_rating": False,
                "space_interval_rating": False,
                "empty_line_interval_rating": False,
                "segment_length": False,
                "segment_strict": False,
                "loop": False,
            }
    
            for line in lines:
                stripped = line.strip()
    
                # Check if we're past the config section
                if stripped.startswith("---") or (
                    stripped and not stripped.startswith("#") and "=" not in stripped
                ):
                    config_section = False
                    # Insert missing configs ONCE when we first exit config section
                    if any(not v for v in config_updated.values()):
                        insert_lines: list[str] = []
                        if not config_updated["speed_multiplier"]:
                            insert_lines.append(
                                f"SPEED_MULTIPLIER = {speed_multiplier}"
                            )
                        if not config_updated["arpeggio_interval"]:
                            insert_lines.append(
                                f"ARPEGGIO_INTERVAL = {arpeggio_interval}"
                            )
                        if not config_updated["arpeggio_auto"]:
                            insert_lines.append(f"ARPEGGIO_AUTO = {arpeggio_auto}")
                        if not config_updated["interval_rating"]:
                            insert_lines.append(f"INTERVAL_RATING = {interval_rating}")
                        if not config_updated["line_interval_rating"]:
                            insert_lines.append(
                                f"LINE_INTERVAL_RATING = {line_interval_rating}"
                            )
                        if not config_updated["space_interval_rating"]:
                            insert_lines.append(
                                f"SPACE_INTERVAL_RATING = {space_interval_rating}"
                            )
                        if not config_updated["empty_line_interval_rating"]:
                            insert_lines.append(
                                f"EMPTY_LINE_INTERVAL_RATING = {empty_line_interval_rating}"
                            )
                        if not config_updated["segment_length"]:
                            insert_lines.append(f"SEGMENT_LENGTH = {segment_length}")
                        if not config_updated["segment_strict"]:
                            insert_lines.append(f"SEGMENT_STRICT = {segment_strict}")
                        if not config_updated["loop"]:
                            insert_lines.append(f"LOOP = {loop}")
    
                        if insert_lines:
                            # Insert before the separator or first score line
                            for insert_line in insert_lines:
                                new_lines.append(insert_line)
    
                        # Mark all as updated
                        for key in config_updated:
                            config_updated[key] = True
    
                if config_section and "=" in line:
                    key, _ = line.split("=", 1)
                    key = key.strip().lower()
    
                    if key == "speed_multiplier":
                        new_lines.append(f"SPEED_MULTIPLIER = {speed_multiplier}")
                        config_updated["speed_multiplier"] = True
                    elif key == "arpeggio_interval":
                        new_lines.append(f"ARPEGGIO_INTERVAL = {arpeggio_interval}")
                        config_updated["arpeggio_interval"] = True
                    elif key == "arpeggio_auto":
                        new_lines.append(f"ARPEGGIO_AUTO = {arpeggio_auto}")
                        config_updated["arpeggio_auto"] = True
                    elif key == "interval_rating":
                        new_lines.append(f"INTERVAL_RATING = {interval_rating}")
                        config_updated["interval_rating"] = True
                    elif key == "line_interval_rating":
                        new_lines.append(
                            f"LINE_INTERVAL_RATING = {line_interval_rating}"
                        )
                        config_updated["line_interval_rating"] = True
                    elif key == "space_interval_rating":
                        new_lines.append(
                            f"SPACE_INTERVAL_RATING = {space_interval_rating}"
                        )
                        config_updated["space_interval_rating"] = True
                    elif key == "empty_line_interval_rating":
                        new_lines.append(
                            f"EMPTY_LINE_INTERVAL_RATING = {empty_line_interval_rating}"
                        )
                        config_updated["empty_line_interval_rating"] = True
                    elif key == "segment_length":
                        new_lines.append(f"SEGMENT_LENGTH = {segment_length}")
                        config_updated["segment_length"] = True
                    elif key == "segment_strict":
                        new_lines.append(f"SEGMENT_STRICT = {segment_strict}")
                        config_updated["segment_strict"] = True
                    elif key == "loop":
                        new_lines.append(f"LOOP = {loop}")
                        config_updated["loop"] = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
    
            # Write back to file
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
    
            # Update original content
            self.original_content = "\n".join(new_lines)
    
    
            self._flash("Configuration saved")
    
        except Exception:
            self._flash("Save failed - see terminal for details")
    
    
    
    def reload(self) -> None:
        """Reload the score file from disk (re-read and re-parse)."""
        if not self.player:
            return
    
        try:
            # Stop current playback
            was_playing = self.player.get_state() == PSM_State.PLAYING
            sustain_enabled = self.player.get_sustain_enabled()
            bookmark = self.player.get_bookmark()
            self.player.stop()
    
            # Re-read file content (utf-8-sig tolerates a BOM)
            with open(self.file_path, "r", encoding="utf-8-sig") as f:
                self.original_content = f.read()
    
            # Re-parse the score (will read config from file)
            parser = ScoreParser(self.file_path)
            self.score = parser.parse()
    
            # Create new player with new score (uses config from parsed score)
            keyboard_controller = KeyboardController()
            self.player = Player(self.score, keyboard_controller, self.key_mapping)
            self.player.set_progress_callback(self._on_progress)
            if sustain_enabled:
                self.player.toggle_sustain()
            self.player.restore_bookmark(bookmark)
    
            # Re-initialize plugins with new player
            # Force re-initialization by updating context and calling initialize directly
    
            plugin_errors = self._reinitialize_plugins()
    
            # Resume playback if it was playing
            if was_playing:
                self.player.play()
    
            self._flash(self._reload_message("Score reloaded", plugin_errors))
    
        except Exception:
            self._flash("Reload failed")
    
    
    
    def _reinitialize_plugins(self) -> int:
        """Point all loaded plugins at the current player and CLI.
    
        Returns:
            Number of plugins that failed to re-initialize
        """
        from src.plugins.core.manager import get_plugin_manager
        from src.plugins.core.context import PluginContext
    
        plugin_manager = get_plugin_manager()
        new_context = PluginContext(
            player=self.player,
            cli=self,
            controller=self.controller,
        )
        plugin_manager.set_context(new_context)
    
        failures = 0
        for plugin in plugin_manager.get_all_plugins():
            try:
                plugin.initialize(new_context)
            except Exception:
                failures += 1
        return failures
    
    
    
    @staticmethod
    def _reload_message(base: str, plugin_errors: int) -> str:
        """Compose a status message, mentioning plugin failures if any."""
        if plugin_errors:
            return f"{base} ({plugin_errors} plugin error{'s' if plugin_errors != 1 else ''})"
        return base
    
    
    
    def reparse(self, message: str = "Score reparsed") -> None:
        """Reparse the score with current configuration (apply new segment_length, etc.)."""
        if not self.player:
            return
    
        try:
            # Get current playback state and position
            was_playing = self.player.get_state() == PSM_State.PLAYING
            current_line, _ = self.player.get_progress()
    
            # Get current configuration
            speed_multiplier = self.player._speed_multiplier
            arpeggio_interval = self.player._arpeggio_interval
            arpeggio_auto = self.player.get_arpeggio_auto()
            interval_rating = self.player._interval_rating
            line_interval_rating = self.player._line_interval_rating
            space_interval_rating = self.player._space_interval_rating
            empty_line_interval_rating = self.player._empty_line_interval_rating
            segment_length = self.player._segment_length
            segment_strict = self.player.get_segment_strict()
            sustain_enabled = self.player.get_sustain_enabled()
            loop_enabled = self.player.get_loop_enabled()
            bookmark = self.player.get_bookmark()
    
            # Stop current playback
            self.player.stop()
    
            # Save current config to file first
            self.save_config()
    
            # Re-parse the score (will use updated config from file)
            parser = ScoreParser(self.file_path)
            self.score = parser.parse()
    
            # Create new player with reparsed score
            keyboard_controller = KeyboardController()
            self.player = Player(self.score, keyboard_controller, self.key_mapping)
            self.player.set_progress_callback(self._on_progress)
    
            plugin_errors = self._reinitialize_plugins()
    
            # Restore configuration (in case file save failed)
            self.player.set_speed(speed_multiplier)
            self.player.set_arpeggio_interval(arpeggio_interval)
            self.player.set_arpeggio_auto(arpeggio_auto)
            self.player.set_interval_rating(interval_rating)
            self.player.set_line_interval_rating(line_interval_rating)
            self.player.set_space_interval_rating(space_interval_rating)
            self.player.set_empty_line_interval_rating(empty_line_interval_rating)
            self.player.set_segment_length(segment_length)
            self.player.set_segment_strict(segment_strict)
            self.player.set_loop_enabled(loop_enabled)
            self.player.restore_bookmark(bookmark)
            if sustain_enabled:
                self.player.toggle_sustain()
    
            # Restore position (clamp to new score length)
            if self.score and current_line < len(self.score.lines):
                self.player.jump_to_line(current_line)
    
            # Resume playback if it was playing
            if was_playing:
                self.player.play()
    
            self._flash(self._reload_message(message, plugin_errors))
    
        except Exception:
            self._flash("Reparse failed")
    
    
