"""Tela (Tkinter) para mapear os controles do robô no joystick.

Selecione um campo e pressione o botão ou mova o eixo desejado. Para os
controles de motor o sentido do eixo é gravado; para a câmera o eixo é usado
nos dois sentidos.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import pygame

from .bindings import CONTROLS, Binding, ControlKind
from .joystick import JoystickDevice, init_pygame
from .settings import Settings, save_bindings

POLL_INTERVAL_MS = 15
CAPTURE_THRESHOLD = 0.6  # quanto o eixo precisa se afastar do repouso
REARM_THRESHOLD = 0.3  # volta ao repouso antes de capturar o mesmo eixo de novo


class JoystickConfigWindow:
    def __init__(self, settings: Settings) -> None:
        init_pygame()
        self._device = JoystickDevice(settings.joystick_index)
        self._rest: list[float] = []
        self._held_axes: set[int] = set()
        self.saved = False

        self.root = tk.Tk()
        self.root.title("Configurar Joystick")
        self.root.resizable(False, False)
        frame = tk.Frame(self.root, padx=12, pady=12)
        frame.grid()

        tk.Label(
            frame,
            text="Selecione um campo e pressione o botão ou mova o eixo do joystick.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self._vars: dict[str, tk.StringVar] = {}
        self._entries: list[tuple[tk.Entry, str]] = []
        for row, control in enumerate(CONTROLS, start=1):
            current = settings.bindings.get(control.key)
            var = tk.StringVar(value=str(current) if current else "")
            tk.Label(frame, text=control.label).grid(row=row, column=0, sticky="w", padx=(0, 8))
            entry = tk.Entry(frame, width=18, textvariable=var)
            entry.grid(row=row, column=1, pady=2)
            self._vars[control.key] = var
            self._entries.append((entry, control.key))

        self._status = tk.StringVar()
        tk.Label(frame, textvariable=self._status, fg="gray").grid(
            row=len(CONTROLS) + 1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        tk.Button(frame, text="Salvar", command=self._save, width=12).grid(
            row=len(CONTROLS) + 2, column=1, sticky="e", pady=(8, 0)
        )

        self._entries[0][0].focus_set()
        self._on_device_changed()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def run(self) -> bool:
        # Lê o joystick no próprio loop do Tk: sem threads mexendo na interface
        self.root.after(POLL_INTERVAL_MS, self._poll)
        self.root.mainloop()
        pygame.quit()
        return self.saved

    def _on_device_changed(self) -> None:
        joystick = self._device.joystick
        if joystick is None:
            self._rest = []
            self._status.set("Conecte um joystick...")
            return
        # Valor de repouso de cada eixo (gatilhos costumam repousar em -1)
        self._rest = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
        self._held_axes.clear()
        self._status.set(f"Joystick: {joystick.get_name()}")

    def _poll(self) -> None:
        for event in pygame.event.get():
            if self._device.handle_event(event):
                self._on_device_changed()
            elif event.type == pygame.JOYBUTTONDOWN:
                self._capture(Binding("button", event.button))
            elif event.type == pygame.JOYAXISMOTION and event.axis < len(self._rest):
                self._on_axis(event.axis, event.value)
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _on_axis(self, axis: int, value: float) -> None:
        delta = value - self._rest[axis]
        if axis in self._held_axes:
            if abs(delta) < REARM_THRESHOLD:
                self._held_axes.discard(axis)
            return
        if abs(delta) >= CAPTURE_THRESHOLD:
            self._held_axes.add(axis)
            self._capture(Binding("axis", axis, 1 if value > 0 else -1))

    def _capture(self, binding: Binding) -> None:
        focused = self.root.focus_get()
        for position, (entry, key) in enumerate(self._entries):
            if entry is not focused:
                continue
            control = CONTROLS[position]
            if control.kind is ControlKind.ANALOG:
                if binding.kind != "axis":
                    self._status.set(f"{control.label} precisa de um eixo analógico")
                    return
                binding = Binding("axis", binding.index)
            self._vars[key].set(str(binding))
            # Avança para o próximo campo
            next_entry = self._entries[(position + 1) % len(self._entries)][0]
            next_entry.focus_set()
            return

    def _save(self) -> None:
        bindings: dict[str, Binding] = {}
        for control in CONTROLS:
            text = self._vars[control.key].get().strip()
            if not text:
                messagebox.showerror("Configurar Joystick", f"Defina: {control.label}")
                return
            try:
                binding = Binding.parse(text)
            except ValueError as exc:
                messagebox.showerror("Configurar Joystick", f"{control.label}: {exc}")
                return
            if control.kind is ControlKind.ANALOG and binding.kind != "axis":
                messagebox.showerror(
                    "Configurar Joystick", f"{control.label} precisa de um eixo analógico"
                )
                return
            bindings[control.key] = binding
        save_bindings(bindings)
        self.saved = True
        self.root.destroy()


def run_config(settings: Settings) -> bool:
    """Abre a tela de configuração. Retorna True se o usuário salvou."""
    return JoystickConfigWindow(settings).run()
