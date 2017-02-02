package org.usfirst.frc.team4183.robot.commands.GearHandlerSubsystem;

import org.usfirst.frc.team4183.robot.OI;
import org.usfirst.frc.team4183.robot.Robot;
import org.usfirst.frc.team4183.utils.CommandUtils;

import edu.wpi.first.wpilibj.command.Command;

/**
 *
 */
public class Idle extends Command {

    public Idle() {
        requires(Robot.gearHandlerSubsystem);
    }

    // Called just before this Command runs the first time
    protected void initialize() {
    }

    // Called repeatedly when this Command is scheduled to run
    protected void execute() {
    }

    // Make this return true when this Command no longer needs to run execute()
    protected boolean isFinished() {
    	if(OI.btnWaitingForBalls.get()) {
    		return CommandUtils.stateChange(this, new GateOpen());
    	}
    	else if(OI.btnWaitingForGear.get()) {
    		return CommandUtils.stateChange(this, new WaitingForGear());
    	}
    	else if(OI.btnOpenGate.get()) {
    		return CommandUtils.stateChange(this, new WaitingForBalls());
    	}
        return false;
    }

    // Called once after isFinished returns true
    protected void end() {
    }

    // Called when another command which requires one or more of the same
    // subsystems is scheduled to run
    protected void interrupted() {
    	end();
    }
}