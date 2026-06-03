import string
import sys
import cozmo
from cozmo.util import degrees, speed_mmps, distance_mm
from openai import OpenAI
import re
import datetime
import random
import speech_recognition as sr
import keyboard
import asyncio
import time
from api_secrets import API_KEY, API_BASE_URL
from character_prompts import cozmo_prompt, hal_prompt, kitt_prompt, jarvis_prompt

# Set Debug mode on or off
Viewer = False
Viewer3d = False

# Speech to Text mode and PTT on/off
ptt = False
longspeech = True

# Streamlit or viewer
if not Viewer:
    import streamlit as st

# Set Default Locale
locale = 'en-US'

# Instantiate the OpenAI Client
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

# Define your model name
MODEL_NAME = "openai/gpt-oss-20b" 

# Choose character and define name + starting prompt
character = 'Cozmo'

# Cozmo
if character == 'Cozmo':
    character_name = 'Cozmo'
    your_name = 'Human'
    cozmo_voice = True
    voice_speed = 0.7
    start_prompt = cozmo_prompt
    wakeup_sequence = 'ConnectWakeUp'
    goodnight_sequence = 'CodeLabSleep'
    character_temp = 0.9
    startup_text = 'Good morning, Human.'
    driving_anim = True

# HAL 9000
elif character == 'HAL':
    character_name = 'HAL 9000'
    your_name = 'Dave'
    cozmo_voice = False
    voice_speed = 0.5
    start_prompt = hal_prompt
    wakeup_sequence = 'DroneModeIdle' 
    goodnight_sequence = 'AcknowledgeFaceInitPause'
    character_temp = 0.9
    startup_text = 'Good morning, Dave.'
    driving_anim = False

# KITT
elif character == 'KITT':
    character_name = 'KITT'
    your_name = 'Michael Knight'
    cozmo_voice = False
    voice_speed = 0.5
    start_prompt = kitt_prompt
    wakeup_sequence = 'DroneModeIdle'
    goodnight_sequence = 'AcknowledgeFaceInitPause'
    character_temp = 0.9
    startup_text = 'Good morning, Michael.'
    driving_anim = False

# Jarvis
elif character == 'Jarvis':
    character_name = 'Jarvis'
    your_name = 'Tony'
    cozmo_voice = False
    voice_speed = 0.5
    start_prompt = jarvis_prompt
    wakeup_sequence = 'DroneModeIdle'
    goodnight_sequence = 'AcknowledgeFaceInitPause'
    character_temp = 0.9
    startup_text = 'Good morning, Tony.'
    driving_anim = False

else:
    print("Invalid character.")

# --- AUXILIARY FUNCTIONS --- #

def recognize_from_microphone(locale_code):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        if not Viewer:
            st.markdown('<strong><font color="green">Speak now!</font></strong>\n', unsafe_allow_html=1)
        
        print("Speak now! (Listening until you stop talking...)")
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            print("Processing speech...")
            text = recognizer.recognize_google(audio, language=locale_code)
            print("Recognized: {}".format(text))
            return text
            
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return ""
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return ""
        except sr.RequestError as e:
            print("API Error: {}".format(e))
            return ""

def recognize_from_microphone_short(locale_code):
    return recognize_from_microphone(locale_code)

def extract_commands(text):
    """Safely extracts commands using regex."""
    if not text: return []
    # Finds all instances of strings starting with -- followed by letters, numbers, underscores, or hyphens
    return re.findall(r'--[A-Za-z0-9_-]+', text)

def remove_commands(text):
    """Filters commands out so Cozmo speaks clean text."""
    if not text: return ""
    text = text.replace(" AI ", " A.I. ")
    
    # Replace the command and surrounding spaces with a single space
    text = re.sub(r'\s*--[A-Za-z0-9_-]+\s*', ' ', text)
    # Clean up any orphaned punctuation 
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    return text.strip()

class BlinkyCube(cozmo.objects.LightCube):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._chaser = None

    def start_light_chaser(self):
        if self._chaser:
            raise ValueError("Light chaser already running")
        async def _chaser():
            while True:
                for i in range(4):
                    cols = [cozmo.lights.off_light] * 4
                    cols[i] = cozmo.lights.blue_light
                    self.set_light_corners(*cols)
                    await asyncio.sleep(0.1, loop=self._loop)
        self._chaser = asyncio.ensure_future(_chaser(), loop=self._loop)

    def stop_light_chaser(self):
        if self._chaser:
            self._chaser.cancel()
            self._chaser = None

cozmo.world.World.light_cube_factory = BlinkyCube

async def kitt_lights(robot: cozmo.robot.Robot):
    outer_left_light = cozmo.lights.off_light
    left_light = cozmo.lights.off_light
    middle_light = cozmo.lights.off_light
    right_light = cozmo.lights.off_light
    outer_right_light = cozmo.lights.off_light

    while True:
        robot.set_backpack_lights(outer_left_light, left_light, middle_light, right_light, outer_right_light)
        left_light = cozmo.lights.Light(on_color=cozmo.lights.red, on_period_ms=500, off_period_ms=500, transition_off_period_ms=150, transition_on_period_ms=150)
        middle_light = cozmo.lights.off_light
        right_light = cozmo.lights.off_light
        await asyncio.sleep(0.7)

        robot.set_backpack_lights(outer_left_light, left_light, middle_light, right_light, outer_right_light)
        left_light = cozmo.lights.off_light
        middle_light = cozmo.lights.Light(on_color=cozmo.lights.red, on_period_ms=500, off_period_ms=500, transition_off_period_ms=150, transition_on_period_ms=150)
        right_light = cozmo.lights.off_light
        await asyncio.sleep(0.7)

        robot.set_backpack_lights(outer_left_light, left_light, middle_light, right_light, outer_right_light)
        left_light = cozmo.lights.off_light
        middle_light = cozmo.lights.off_light
        right_light = cozmo.lights.Light(on_color=cozmo.lights.red, on_period_ms=500, off_period_ms=500, transition_off_period_ms=150, transition_on_period_ms=150)
        await asyncio.sleep(0.7)

        robot.set_backpack_lights(outer_left_light, left_light, middle_light, right_light, outer_right_light)
        left_light = cozmo.lights.off_light
        middle_light = cozmo.lights.Light(on_color=cozmo.lights.red, on_period_ms=500, off_period_ms=500, transition_off_period_ms=150, transition_on_period_ms=150)
        right_light = cozmo.lights.off_light
        await asyncio.sleep(0.7)

if not Viewer:
    st.title('Chat with ' + character_name + '!')
    st.markdown('<strong><font color="yellow">Wait for the "Press Spacebar to speak" indication to interact with ' + character_name + '.</font></strong>\n', unsafe_allow_html=1)

def cozmo_GPT(robot: cozmo.robot.Robot):

    robot.camera.color_image_enabled = True

    # --- INTERNAL FUNCTIONS --- #
    def facefinder():
        time.sleep(0.5)
        lookaround = robot.start_behavior(cozmo.behavior.BehaviorTypes.FindFaces)
        if not Viewer:
            st.markdown('<strong><font color="cyan">' + character_name + ' is looking for your face...</font></strong>\n', unsafe_allow_html=1)

        face_to_follow = None

        while True:
            turn_action = None
            if face_to_follow:
                lookaround.stop()
                turn_action = robot.turn_towards_face(face_to_follow)
                if not Viewer:
                    st.markdown('<strong><font color="green">' + character_name + ' found your face</font></strong>\n', unsafe_allow_html=1)
                time.sleep(2)
                return

            if not (face_to_follow and face_to_follow.is_visible):
                try:
                    face_to_follow = robot.world.wait_for_observed_face(timeout=10)
                except asyncio.TimeoutError:
                    if not Viewer:
                        st.markdown('<strong><font color="red">' + character_name + ' Did not find your face. Ask "Look at me" to try again.</font></strong>\n', unsafe_allow_html=1)
                    lookaround.stop()
                    time.sleep(0.3)
                    robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
                    return

            if turn_action:
                turn_action.wait_for_completed()

            time.sleep(.1)

    def character_lights():
        if character_name == 'Cozmo':
            robot.set_all_backpack_lights(cozmo.lights.Light(on_color=cozmo.lights.white))
        if character_name == 'KITT':
            robot.set_center_backpack_lights(cozmo.lights.Light(on_color=cozmo.lights.red, on_period_ms=500, off_period_ms=500, transition_off_period_ms=150, transition_on_period_ms=150))
        if character_name == 'HAL 9000':
            robot.set_all_backpack_lights(cozmo.lights.Light(on_color=cozmo.lights.red))
        if character_name == 'Jarvis':
            robot.set_center_backpack_lights(cozmo.lights.Light(on_color=cozmo.lights.green, on_period_ms=500, off_period_ms=500, transition_off_period_ms=150, transition_on_period_ms=150))

    def writelog(logline):
        now = datetime.datetime.now()
        date_time_string = now.strftime("%B %d, %Y %H:%M:%S")
        with open("log.txt", "a", encoding="utf-8") as file:
            if logline == '\n-----------------------------------------------------------------------------------------------\n\n':
                file.write(str(logline + date_time_string + ' > NEW '+ character_name.upper() +' CONVERSATION LOG:\n'))
            else:
                if logline.startswith('\n'):
                    logline = logline[1:]
                file.write(str('\n' + logline))

    def getcube():
        robot.set_lift_height(0.0).wait_for_completed()
        robot.set_head_angle(degrees(0)).wait_for_completed()

        look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)
        cube = None

        try:
            cube = robot.world.wait_for_observed_light_cube(timeout=5)
            print("Found cube: %s" % cube)
        except asyncio.TimeoutError:
            print("Didn't find a cube")
            look_around.stop()
            if character_name == "HAL 9000":
                robot.say_text('No asteroids found in the area, all clear.', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "KITT":
                robot.say_text('No suspicious activity found.', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "Cozmo":
                robot.say_text("I can't see any cube!", play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "Jarvis":
                robot.say_text("The ARC reactor is not in this area, Tony.", play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
        finally:
            time.sleep(0.3)
            look_around.stop()

        if cube:
            print("Cozmo found a cube")
            cube.start_light_chaser()
            if character_name == "HAL 9000":
                robot.say_text('Asteroid found, getting closer to investigate.', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "KITT":
                robot.say_text('Suspicious activity found. Investigating.', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "Cozmo":
                robot.say_text("Cube found!", play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "Jarvis":
                robot.say_text("ARC reactor found!", play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            
            action = robot.roll_cube(cube, check_for_object_on_top=True, num_retries=5)
            action.wait_for_completed()
            
            if character_name == "HAL 9000":
                robot.say_text('Scan complete. No anomalies found. Going back to normal operation', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "KITT":
                robot.say_text('Nothing to report.', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "Cozmo":
                robot.say_text("I love my cubes!", play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            if character_name == "Jarvis":
                robot.say_text("Arc reactor activated!", play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            
            time.sleep(0.3)
            robot.drive_straight(distance_mm(-100), speed_mmps(70), should_play_anim=False).wait_for_completed()
            cube.stop_light_chaser()
            cube.set_lights_off()
    
    def docking():
        robot.set_lift_height(0.0).wait_for_completed()
        robot.set_head_angle(degrees(0)).wait_for_completed()

        look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)
        try:
            cube = robot.world.wait_for_observed_light_cube(timeout=30)
            print("Found cube: %s" % cube)
        except asyncio.TimeoutError:
            print("Didn't find a cube")
        finally:
            look_around.stop()

        if cube:
            print("Cozmo found a cube, and will now attempt to dock with it:")
            cube.start_light_chaser()
            action = robot.dock_with_cube(cube, approach_angle=cozmo.util.degrees(0), num_retries=2)
            action.wait_for_completed()
            print("result:", action.result)
            robot.set_lift_height(1.0).wait_for_completed()
            if not Viewer:
                st.markdown("'Docking Complete")
            robot.say_text('Docking Complete!', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            robot.set_lift_height(0.0).wait_for_completed()
            robot.drive_straight(distance_mm(-100), speed_mmps(70), should_play_anim=False).wait_for_completed()
            cube.stop_light_chaser()
            cube.set_lights_off()

    def boost():
        robot.set_lift_height(0.0).wait_for_completed()
        robot.set_head_angle(degrees(0)).wait_for_completed()
        time.sleep(0.3)

        look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)
        cube = None

        try:
            cube = robot.world.wait_for_observed_light_cube(timeout=30)
            print("Found cube: %s" % cube)
        except asyncio.TimeoutError:
            print("Didn't find a cube")
        finally:
            look_around.stop()

        if cube:
            cube.start_light_chaser()
            action = robot.pop_a_wheelie(cube, num_retries=2)
            action.wait_for_completed()
            print("Completed action: result = %s" % action)
            cube.stop_light_chaser()
            cube.set_lights_off()

    def character_commands(command, cleanreply='', animation=driving_anim):
        
        if command == '--La':
            robot.play_anim(name='anim_poked_giggle').wait_for_completed()
            time.sleep(0.3)
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** laughs **")
        
        if command == '--Cr':
            robot.play_anim_trigger(cozmo.anim.Triggers.MemoryMatchPlayerLoseHandSolo, ignore_body_track=False, in_parallel=False).wait_for_completed()
            time.sleep(0.3)
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** cries **")

        if command == '--Fu':
            robot.play_anim_trigger(cozmo.anim.Triggers.PeekABooGetOutHappy, ignore_body_track=False, in_parallel=False).wait_for_completed()
            time.sleep(0.3)
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** has fun **")

        if command == '--Sa':
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabLose, ignore_body_track=False, in_parallel=False).wait_for_completed()
            robot.turn_in_place(degrees(-65)).wait_for_completed()
            time.sleep(0.3)
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** is sad **")

        if command == '--Sc':
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabScaredCozmo, ignore_body_track=False, in_parallel=False).wait_for_completed()
            time.sleep(0.3)
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** is scared **")
        
        if command == '--Po':
            if random.random() < 0.33:
                robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabZombie, ignore_body_track=False, in_parallel=False).wait_for_completed()
            
            robot.set_lift_height(0.0).wait_for_completed()
            robot.set_lift_height(1.0).wait_for_completed()
            time.sleep(0.2)
            robot.drive_wheel_motors(-70, -20)
            
            # Use cleanreply to speak while possessed
            if cleanreply:
                robot.say_text(cleanreply[:245], play_excited_animation=False, use_cozmo_voice=False, duration_scalar=0.7, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
            
            robot.stop_all_motors()
            time.sleep(0.2)
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            time.sleep(0.2)
            robot.set_lift_height(0.0).wait_for_completed()
            time.sleep(0.2)
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** needs an exorcism **")

        if command.startswith('--Lo'):
            subcommands = command.split("_")
            if len(subcommands) > 1:
                global locale
                locale = subcommands[1]
        
        if command == '--H_u':
            robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
        
        if command == '--H_d':
            robot.set_head_angle(cozmo.robot.MIN_HEAD_ANGLE).wait_for_completed()

        if command == '--Fl_u':
            robot.set_lift_height(1.0).wait_for_completed()
        
        if command == '--Fl_d':
            robot.set_lift_height(0.0).wait_for_completed()

        if command.startswith('--DF'):
            subcommands = command.split("_")
            if len(subcommands) > 1:
                distance = int(subcommands[1])
                speed = int(subcommands[2])
                robot.drive_straight(distance_mm(distance), speed_mmps(speed), should_play_anim=animation).wait_for_completed()
                time.sleep(0.3)
                robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

        if command.startswith('--DB'):
            subcommands = command.split("_")
            if len(subcommands) > 1:
                distance = int(subcommands[1].replace(".", "").replace('"', "").replace("'", ""))
                speed = int(subcommands[2].replace(".", "").replace('"', "").replace("'", ""))
                robot.drive_straight(distance_mm(-distance), speed_mmps(speed), should_play_anim=animation).wait_for_completed()
                time.sleep(0.3)
                robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

        if command.startswith('--ST'):
            subcommands = command.split("_")
            if len(subcommands) > 1:
                degreez = -(int(subcommands[1].replace(".", "").replace('"', "").replace("'", "")))
                robot.turn_in_place(degrees(degreez)).wait_for_completed()
                time.sleep(0.3)
                robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

        if command == '--Boost':
            boost()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** uses Turbo Boost **")

        if command == '--Ro':
            getcube()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** is looking for objects **")

        if command == '--Do':
            docking()
            if not Viewer:
                st.markdown('\n'+ character_name +': ' + "** is docking **")
        
        if command == '--Bat':
            batt = str(round(robot.battery_voltage, 2))
            if not Viewer:
                st.markdown(' ' + batt + "V")
            robot.say_text(batt + ' volts', play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()

    # --- INITIALIZATION --- #

    writelog('\n-----------------------------------------------------------------------------------------------\n\n')

    robot.set_lift_height(0.0).wait_for_completed()
    robot.play_anim_trigger(cozmo.anim.Triggers.ConnectWakeUp, ignore_body_track=False, in_parallel=False).wait_for_completed()
    character_lights()
    facefinder()

    # Change 1: Refactor to structured message history to prevent AI hallucinations
    message_history = []
    message_history.append({"role": "user", "content": "System initialization complete. Wake up and briefly greet the human."})

    # Initial API Call
    try:
        gptresponse = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": start_prompt}] + message_history,
            temperature=character_temp,
            max_tokens=120,
            top_p=0.2,
            frequency_penalty=0,
            presence_penalty=0.6
        )
        reply = gptresponse.choices[0].message.content or ""
        
        # Change 2: Aggressive regex to strip character names, even with markdown bolding or leading newlines
        reply = re.sub(fr'^\s*(\*\*)?{character_name}(\*\*)?\s*:\s*', '', reply, flags=re.IGNORECASE).strip()

    except Exception as e:
        print(f"API Initialization Error: {e}")
        reply = "I am having trouble connecting to my neural net."

    if reply:
        message_history.append({"role": "assistant", "content": reply})
        writelog(reply)
        
        if not Viewer:
            st.markdown('\n' + reply)
        print(f"\n{character_name}: {reply}")

        spoken_text = remove_commands(reply)
        commands = extract_commands(reply)

        if "--Po" not in commands and spoken_text:
            robot.say_text(spoken_text[:245], play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()

        for command in commands:
            character_commands(command, cleanreply=spoken_text)

    # --- MAIN LOOP --- #
    print('\n > ' + character_name + ' starts listening here...')
    while True:
        if not longspeech:
            humanresponse = recognize_from_microphone_short(locale)
        else:
            humanresponse = recognize_from_microphone(locale)

        if humanresponse != '':
            if character_name == 'Cozmo':
                humanresponse = re.sub("cosmo", "Cozmo", humanresponse, flags=re.IGNORECASE)
            if character_name == 'HAL 9000':
                humanresponse = re.sub("Al", "HAL", humanresponse, flags=re.IGNORECASE)
            if character_name == 'KITT':
                humanresponse = re.sub("kid", "KITT", humanresponse, flags=re.IGNORECASE)

            # STOP SEQUENCE #
            if 'good night' in humanresponse.lower() or 'goodnight' in humanresponse.lower():
                writelog("STOP requested by user")
                if character_name == 'Cozmo':
                    goodnight = "Good night to you, my human friend..."
                    robot.say_text(goodnight, play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
                
                if character_name == 'HAL 9000':
                    goodnight = "Dave, please do not deactivate me..."
                    robot.say_text(goodnight, play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
                    goodnight = "Dave, please reconsider... "
                    robot.say_text(goodnight, play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=1, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
                    goodnight = "Dave... please..."
                    robot.say_text(goodnight, play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=1.5, voice_pitch=-500, in_parallel=False, num_retries=0).wait_for_completed()
                    goodnight = "Dave"
                    robot.say_text(goodnight, play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=2, voice_pitch=-1000, in_parallel=False, num_retries=0).wait_for_completed()
                
                if character_name == 'KITT':
                    goodnight = 'See you on the next mission, Michael!'
                    robot.say_text(goodnight, play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()

                if character_name == 'Jarvis':
                    goodnight = 'See you on the next Avengers mission, Tony!'
                    robot.say_text(goodnight, play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()
                  
                robot.play_anim_trigger(getattr(cozmo.anim.Triggers, goodnight_sequence), ignore_body_track=False, in_parallel=False).wait_for_completed()
                
                if not Viewer:
                    st.stop()
                sys.exit()

            if 'look at me' in humanresponse.lower():
                facefinder()

            # Record human input to structured array and log
            message_history.append({"role": "user", "content": humanresponse})
            writelog(your_name + ": " + humanresponse)

            print('\n' + your_name + ': ' + humanresponse)
            if not Viewer:
                st.markdown(your_name + ": " + humanresponse)

            # Main Conversation API Call
            try:
                gptresponse = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "system", "content": start_prompt}] + message_history,
                    temperature=character_temp,
                    max_tokens=120,
                    top_p=0.2,
                    frequency_penalty=0,
                    presence_penalty=0.6
                )
                reply = gptresponse.choices[0].message.content or ""
                # Strip generated character prefixes comprehensively
                reply = re.sub(fr'^\s*(\*\*)?{character_name}(\*\*)?\s*:\s*', '', reply, flags=re.IGNORECASE).strip()

            except Exception as e:
                print(f"API Error during conversation loop: {e}")
                reply = "I'm sorry, I failed to process that request due to a server error."

            # Output handling system
            if reply != '':
                # Add back to structured history and logs
                message_history.append({"role": "assistant", "content": reply})
                writelog(character_name + ": " + reply)

                # Output to terminal/Streamlit
                print(f"\n{character_name}: {reply}")
                if not Viewer:
                    st.markdown('\n' + reply)

                # Parse the final commands and filter the speaking text
                commands = extract_commands(reply)
                spoken_text = remove_commands(reply)

                # Standard Speech execution
                if "--Po" not in commands and spoken_text:
                    robot.say_text(spoken_text[:245], play_excited_animation=False, use_cozmo_voice=cozmo_voice, duration_scalar=voice_speed, voice_pitch=-100, in_parallel=False, num_retries=0).wait_for_completed()

                # Action Command execution
                if commands:
                    print(f"> Commands detected: {commands}")
                    for command in commands:
                        character_commands(command, cleanreply=spoken_text)
                    character_lights()

            else:
                # Remove the dead prompt from context memory so it doesn't break future turns
                message_history.pop()
                reply = f'** {character_name} is silent **'
                writelog(reply)
                print(f"\n{reply}")
                if not Viewer:
                    st.markdown(reply)

cozmo.run_program(cozmo_GPT, use_3d_viewer=Viewer3d, use_viewer=Viewer, force_viewer_on_top=True)