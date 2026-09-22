"""Shared handling for members who have no row in the `members` table yet.

Rows come from two places: welcome.py creates one on_member_join, and levels.py
creates one on a member's first message. Neither is a guarantee -

  * anyone already in the guild before the bot joined never fired on_member_join,
  * on_member_join needs the members intent and is missed during downtime,
  * a member can be in the guild without having posted.

So every command has to cope with query() returning None. The ones that went
straight to result[0] raised TypeError: 'NoneType' object is not subscriptable.

Keeping the wording in one place stops the several copies of this message from
drifting apart the way the levelling formula did.
"""

NO_RECORD_SELF = (":question:  Hmm, I don't have a record for you yet. "
                  "Say something in the server first and I'll start keeping track.")

NO_RECORD_OTHER = (":question:  Hmm, I can't find a record for {display_name}. "
                   "Have they spoken in this server before?")


def no_record_message(display_name=None) -> str:
    """The reply for a missing members row.

    Pass the member's display name when the missing record belongs to someone
    else, or nothing when it belongs to whoever ran the command - "have they
    spoken here before?" reads oddly when addressed to the person themselves.
    """
    if display_name is None:
        return NO_RECORD_SELF
    return NO_RECORD_OTHER.format(display_name=display_name)


async def send_no_record(interaction, display_name=None, delete_after=None) -> None:
    """Reply to `interaction` explaining that there is no record to read."""
    await interaction.response.send_message(no_record_message(display_name),
                                            ephemeral=True, delete_after=delete_after)
