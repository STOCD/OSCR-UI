from .translation import init_translation

def init_header_trans(language):
    global _
    _ = init_translation(language)

def get_table_headers():
    return (
        _('Combat Time'), _('DPS'), _('Total Damage'), _('Debuff'), _('Attacks-in Share'),
        _('Taken Damage Share'), _('Damage Share'), _('Max One Hit'), _('Crit Chance'), _('Deaths'), _('Total Heals'),
        _('Heal Share'), _('Heal Crit Chance'), _('Total Damage Taken'), _('Total Hull Damage Taken'),
        _('Total Shield Damage Taken'), _('Total Attacks'), _('Hull Attacks'), _('Attacks-in Number'),
        _('Heal Crit Number'), _('Heal Number'), _('Crit Number'), _('Misses')
    )

def get_tree_headers():
    return (
        '', _('DPS'), _('Total Damage'), _('Debuff'), _('Max One Hit'), _('Crit Chance'), _('Accuracy'), _('Flank Rate'),
        _('Kills'), _('Attacks'), _('Misses'), _('Critical Hits'), _('Flank Hits'), _('Shield Damage'), _('Shield DPS'),
        _('Hull Damage'), _('Hull DPS'), _('Base Damage'), _('Base DPS'), _('Combat Time'), _('Hull Attacks'),
        _('Shield Attacks')  # , _('Shield Resistance')
    )

def get_heal_tree_headers():
    return (
        '', _('HPS'), _('Total Heal'), _('Hull Heal'), _('Hull HPS'), _('Shield Heal'), _('Shield HPS'),
        _('Max One Heal'), _('Crit Chance'), _('Heal Ticks'), _('Critical Heals'), _('Combat Time'), _('Hull Heal Ticks'),
        _('Shield Heal Ticks')
    )

def get_live_table_headers():
    return (
        _('DPS'), _('Combat Time'), _('Debuff'), _('Attacks-in'), _('HPS'), _('Kills'), _('Deaths')
    )

def get_ladder_headers():
    return (
        _('Name'), _('Handle'), _('DPS'), _('Total Damage'), _('Deaths'), _('Combat Time'), _('Date'), _('Max One Hit'), _('Debuff'), _('Highest Damage Ability')
    )
