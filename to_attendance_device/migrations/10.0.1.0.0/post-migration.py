
def migrate(cr, version):
    """
    We added protocol switching between UDP and TCP and set TCP as the default value.
    However, existing users who are on UDP may not want this change. This SQL will try
    keep UDP for the existing users.
    """
    cr.execute("""       
        UPDATE attendance_device SET protocol='udp' WHERE id > 1
    """)