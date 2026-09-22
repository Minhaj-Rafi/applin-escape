"""Contain the known Pygame joystick-event conversion failure, not game errors."""
import pygame

RAW_JOYSTICK_EVENTS=tuple(getattr(pygame,n) for n in (
    'JOYAXISMOTION','JOYBALLMOTION','JOYHATMOTION','JOYBUTTONUP','JOYBUTTONDOWN',
    'JOYDEVICEADDED','JOYDEVICEREMOVED'))
CONTROLLER_EVENTS=tuple(getattr(pygame,n) for n in (
    'CONTROLLERAXISMOTION','CONTROLLERBUTTONDOWN','CONTROLLERBUTTONUP',
    'CONTROLLERDEVICEADDED','CONTROLLERDEVICEREMOVED','CONTROLLERDEVICEREMAPPED'))

def configure_events():
    # Controllers are polled in controls.py. Keeping SDL's joystick/controller
    # events out of the Python queue avoids the Windows KeyError(0) conversion
    # fault while retaining live axes and buttons through SDL's device state.
    pygame.event.set_blocked(RAW_JOYSTICK_EVENTS+CONTROLLER_EVENTS)

def known_conversion_failure(exc):
    cause=exc.__cause__ or exc.__context__
    return (isinstance(exc,SystemError) and 'returned a result with an exception set' in str(exc)
            and isinstance(cause,KeyError) and cause.args==(0,))

def read_events(app):
    try: return pygame.event.get()
    except SystemError as exc:
        if not known_conversion_failure(exc) or getattr(app,'input_recovered',False): raise
        # One recovery only. Unrelated or repeated failures retain their traceback.
        app.input_recovered=True
        pygame.event.set_blocked(RAW_JOYSTICK_EVENTS+CONTROLLER_EVENTS)
        app.controls.disable_gamepads()
        app.input_notice='Controller event error: keyboard and mouse active. Restart to retry controllers.'
        if app.screen=='play': app.action('pause')
        app.save_expedition()
        print(app.input_notice)
        return []
