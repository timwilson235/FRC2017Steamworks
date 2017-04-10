package org.usfirst.frc.team4183.utils;


public class PWM {
	
	public interface User {
		public void set( double val);
	}

	private long periodMsecs;
	private User user;
	private double maxDrive;
	private volatile double val;
	private PWMThread loopThread;
	

	public PWM( double freqHz, double maxDrive, User user) {
		periodMsecs = Math.round(1000.0/Math.abs(freqHz));
		this.maxDrive = Math.min(1.0, Math.abs(maxDrive));
		this.user = user;
		this.val = 0.0;

		loopThread = new PWMThread();
		loopThread.setPriority(Thread.NORM_PRIORITY+3);
	}
	
	public void start() {
		val = 0.0;
		loopThread.start();
	}

	public void stop() {
		// Signal loop thread to quit
		loopThread.quit();
		
		// Wait for thread to exit
		try {
			loopThread.join();
		} catch (InterruptedException e) {
			// Per this excellent article:
			// http://www.ibm.com/developerworks/library/j-jtp05236/
			Thread.currentThread().interrupt();
		}
		
		val = 0.0;
		user.set(val);
	}
	
	public void set( double val) {
		val = Math.signum(val)*Math.min(Math.abs(val), 1.0);
		this.val = val;
	}
	
	
	private class PWMThread extends Thread {
		
		private void quit() {
			interrupt();
		}

		@Override
		public void run() {

			// Loop 'til interrupted
			try {
				while( true) {

					long onMsecs = Math.round(periodMsecs * Math.min(Math.abs(val)/maxDrive, 1.0));
					long offMsecs = Math.max(0, periodMsecs - onMsecs);				
					double onVal = Math.signum(val)*Math.max(Math.abs(val), maxDrive);

					if( onMsecs > 0) {
						user.set(onVal);
						Thread.sleep(onMsecs);
					}

					if( offMsecs > 0) {
						user.set(0.0);
						Thread.sleep(offMsecs);
					}
				}
			}
			catch(InterruptedException e) {}
		}
	}
}
