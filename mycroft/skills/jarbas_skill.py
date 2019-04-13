from mycroft.skills.core import MycroftSkill, FallbackSkill, dig_for_message
from mycroft.audio import wait_while_speaking
from mycroft.messagebus.message import Message


#######################################################################
# JarbasSkill base class
#######################################################################
class JarbasSkill(MycroftSkill):
    """
    Abstract base class which provides common behaviour and parameters to all
    Skills implementation. This contains extra features not present in
    MycroftSkill

    New features:
        - converse deactivate handler
        - metadata field in speak and speak_dialog methods
    """

    def bind(self, bus):
        """ Register messagebus emitter with skill.

        Arguments:
            bus: Mycroft messagebus connection
        """
        super().bind(bus)
        if bus:
            self.add_event("converse.deactivate", self._deactivate_skill)

    def _deactivate_skill(self, message):
        skill_id = message.data.get("skill_id")
        if skill_id == self.skill_id:
            self.on_deactivate()

    def on_deactivate(self):
        """
        Invoked when the skill is removed from active skill list
        """
        pass

    def speak(self, utterance, expect_response=False,
              wait=False, metadata=None):
        """ Speak a sentence.

            Args:
                utterance (str):        sentence mycroft should speak
                expect_response (bool): set to True if Mycroft should listen
                                        for a response immediately after
                                        speaking the utterance.
                wait (bool):            set to True to block while the text
                                        is being spoken.
                metadata (dict):        arbitrary data about sentence
                                        e.g. source url
        """
        # registers the skill as being active
        self.enclosure.register(self.name)
        data = {'utterance': utterance,
                'expect_response': expect_response,
                'metadata': metadata or {}}
        message = dig_for_message()

        if message:
            self.bus.emit(message.forward("speak", data))
        else:
            self.bus.emit(Message("speak", data))
        if wait:
            wait_while_speaking()

    def speak_dialog(self, key, data=None, expect_response=False,
                     wait=False, metadata=None):
        """ Speak a random sentence from a dialog file.

            Args:
                key (str): dialog file key (e.g. "hello" to speak from the file
                                            "locale/en-us/hello.dialog")
                data (dict): information used to populate sentence
                expect_response (bool): set to True if Mycroft should listen
                                        for a response immediately after
                                        speaking the utterance.
                wait (bool):            set to True to block while the text
                                        is being spoken.
                metadata (dict):        arbitrary data about sentence
                                        e.g. source url
        """
        data = data or {}
        self.speak(self.dialog_renderer.render(key, data),
                   expect_response, wait, metadata=metadata)


class JarbasFallbackSkill(JarbasSkill, FallbackSkill):
    pass
