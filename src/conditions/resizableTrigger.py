"""Logic for trigger items, allowing them to be resized."""
from conditions import (
    make_result, RES_EXHAUSTED,
)
from instanceLocs import resolve as resolve_inst
from utils import Vec
import utils
import conditions
import vmfLib as VLib
import vbsp

LOGGER = utils.getLogger(__name__, alias='cond.resizeTrig')

@make_result('ResizeableTrigger')
def res_resizeable_trigger(inst: VLib.Entity, res):
    """Replace two markers with a trigger brush.

    This is run once to affect all of an item.
    Options:
    'markerInst': <ITEM_ID:1,2> value referencing the marker instances, or a filename.
    'markerItem': The item's ID
    'previewVar': A stylevar which enables/disables the preview overlay.
    'previewinst': An instance to place at the marker location in preview mode.
        This should contain checkmarks to display the value when testing.
    'previewMat': If set, the material to use for an overlay func_brush.
        The brush will be parented to the trigger, so it vanishes once killed.
        It is also non-solid.
    'previewScale': The scale for the func_brush materials.
    'previewActivate', 'previewDeactivate': The 'instance:name;Input' value
        to turn the previewInst on and off.

    'triggerActivate, triggerDeactivate': The outputs used when the trigger
        turns on or off.

    'triggermat': The texture to assign to the trigger brush (toolstrigger by
        default.)
    'keys': A block of keyvalues for the trigger brush. Origin and targetname
        will be set automatically.
    'localkeys': The same as above, except values will be changed to use
        instance-local names.
    """
    marker = resolve_inst(res['markerInst'])

    markers = {}
    for inst in vbsp.VMF.by_class['func_instance']:
        if inst['file'].casefold() in marker:
            markers[inst['targetname']] = inst

    if not markers:  # No markers in the map - abort
        return RES_EXHAUSTED

    trigger_mat = res['triggermat', 'tools/toolstrigger']
    trig_act = res['triggerActivate', 'OnStartTouchAll']
    trig_deact = res['triggerDeactivate', 'OnEndTouchAll']

    marker_connection = conditions.CONNECTIONS[res['markerItem'].casefold()]
    mark_act_name, mark_act_out = marker_connection.out_act
    mark_deact_name, mark_deact_out = marker_connection.out_deact
    del marker_connection

    preview_var = res['previewVar', ''].casefold()

    # Display preview overlays if it's preview mode, and the style var is true
    # or does not exist
    if vbsp.IS_PREVIEW and (not preview_var or vbsp.settings['style_vars'][preview_var]):
        preview_mat = res['previewMat', '']
        preview_inst_file = res['previewInst', '']
        pre_act_name, pre_act_inp = VLib.Output.parse_name(
            res['previewActivate', ''])
        pre_deact_name, pre_deact_inp = VLib.Output.parse_name(
            res['previewDeactivate', ''])
        preview_scale = utils.conv_float(res['previewScale', '0.25'], 0.25)
    else:
        # Deactivate the preview_ options when publishing.
        preview_mat = preview_inst_file = ''
        pre_act_name = pre_deact_name = None
        pre_act_inp = pre_deact_inp = ''
        preview_scale = 0.25

    # Now convert each brush
    # Use list() to freeze it, allowing us to delete from the dict
    for targ, inst in list(markers.items()):  # type: str, VLib.Entity
        for out in inst.output_targets():
            if out in markers:
                other = markers[out]  # type: VLib.Entity
                del markers[out]  # Don't let it get repeated
                break
        else:
            if inst.fixup['$connectioncount'] == '0':
                # If the item doesn't have any connections, 'connect'
                # it to itself so we'll generate a 1-block trigger.
                other = inst
            else:
                continue  # It's a marker with an input, the other in the pair
                # will handle everything.

        for ent in {inst, other}:
            # Only do once if inst == other
            ent.remove()

        bbox_min, bbox_max = Vec.bbox(
            Vec.from_str(inst['origin']),
            Vec.from_str(other['origin'])
        )

        # Extend to the edge of the blocks.
        bbox_min -= 64
        bbox_max += 64

        trig_ent = vbsp.VMF.create_ent(
            classname='trigger_multiple', # Default
            # Use the 1st instance's name - that way other inputs control the
            # trigger itself.
            targetname=targ,
            origin=inst['origin'],
            angles='0 0 0',
        )
        trig_ent.solids = [
            vbsp.VMF.make_prism(
                bbox_min,
                bbox_max,
                mat=trigger_mat,
            ).solid,
        ]
        # Use 'keys' and 'localkeys' blocks to set all the other keyvalues.
        conditions.set_ent_keys(trig_ent, inst, res)

        if preview_mat:
            preview_brush = vbsp.VMF.create_ent(
                classname='func_brush',
                parentname=targ,
                origin=inst['origin'],

                Solidity='1',  # Not solid
                drawinfastreflection='1',  # Draw in goo..

                # Disable shadows and lighting..
                disableflashlight='1',
                disablereceiveshadows='1',
                disableshadowdepth='1',
                disableshadows='1',
            )
            preview_brush.solids = [
                # Make it slightly smaller, so it doesn't z-fight with surfaces.
                vbsp.VMF.make_prism(
                    bbox_min + 0.5,
                    bbox_max - 0.5,
                    mat=preview_mat,
                ).solid,
            ]
            for face in preview_brush.sides():
                face.scale = preview_scale

        if preview_inst_file:
            preview_inst_ent = vbsp.VMF.create_ent(
                classname='func_instance',
                targetname=targ + '_preview',
                file=preview_inst_file,
                # Put it at the second marker, since that's usually
                # closest to antlines if present.
                origin=other['origin'],
            )

            if pre_act_name:
                trig_ent.outputs.append(VLib.Output(
                    trig_act,
                    targ + '_preview',
                    inst_in=pre_act_name,
                    inp=pre_act_inp,
                ))
            if pre_deact_name:
                trig_ent.outputs.append(VLib.Output(
                    trig_deact,
                    targ + '_preview',
                    inst_in=pre_deact_name,
                    inp=pre_deact_inp,
                ))

        # Now copy over the outputs from the markers, making it work.
        for out in inst.outputs + other.outputs:
            # Skip the output joining the two markers together.
            if out.target == other['targetname']:
                continue

            if out.inst_out == mark_act_name and out.output == mark_act_out:
                trig_out = trig_act
            elif out.inst_out == mark_deact_name and out.output == mark_deact_out:
                trig_out = trig_deact
            else:
                continue  # Skip this output - it's somehow invalid for this item.

            if trig_out == "":
                continue  # Allow setting the output to "" to skip

            trig_ent.outputs.append(VLib.Output(
                trig_out,
                out.target,
                inst_in=out.inst_in,
                inp=out.input,
                param=out.params,
                delay=out.delay,
                times=out.times,
            ))

    return RES_EXHAUSTED
