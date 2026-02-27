import crypto from 'crypto';
import { logger } from '../utils/logger';
import { emailService } from './email.service';

interface OTPRecord {
  otp: string;
  expiresAt: Date;
  email: string;
}

export class OTPService {
  private otpStore: Map<string, OTPRecord> = new Map();
  private readonly OTP_EXPIRY_MINUTES = 10;
  private readonly OTP_LENGTH = 6;

  /**
   * Generate a random 6-digit OTP
   */
  private generateOTP(): string {
    return crypto.randomInt(100000, 999999).toString();
  }

  /**
   * Generate and send OTPs to all admin emails
   */
  async generateAndSendOTPs(adminEmails: string[]): Promise<void> {
    if (!adminEmails || adminEmails.length === 0) {
      throw new Error('No admin emails configured');
    }

    if (adminEmails.length > 5) {
      throw new Error('Maximum 5 admin emails allowed');
    }

    logger.info(`🔐 Generating OTPs for ${adminEmails.length} admin(s)`);

    // Clear any existing OTPs
    this.otpStore.clear();

    const expiresAt = new Date();
    expiresAt.setMinutes(expiresAt.getMinutes() + this.OTP_EXPIRY_MINUTES);

    // Generate OTPs for each admin
    const otpPromises = adminEmails.map(async (email) => {
      const otp = this.generateOTP();
      
      // Store OTP
      this.otpStore.set(email, {
        otp,
        expiresAt,
        email,
      });

      // Send OTP via email
      await this.sendOTPEmail(email, otp, expiresAt);
      
      logger.info(`✅ OTP generated and sent to: ${email.substring(0, 3)}***`);
    });

    await Promise.all(otpPromises);
    
    logger.info(`🎉 All OTPs sent successfully. Valid until: ${expiresAt.toLocaleString()}`);
  }

  /**
   * Send OTP email to admin
   */
  private async sendOTPEmail(email: string, otp: string, expiresAt: Date): Promise<void> {
    const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Restricted Mode OTP</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
          
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 40px 30px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">
                🔐 Restricted Mode Unlock
              </h1>
              <p style="margin: 10px 0 0 0; color: #fee2e2; font-size: 16px;">
                One-Time Password
              </p>
            </td>
          </tr>

          <!-- OTP Display -->
          <tr>
            <td style="padding: 40px 30px; text-align: center;">
              <p style="margin: 0 0 20px 0; font-size: 16px; color: #374151;">
                Your OTP to disable restricted mode:
              </p>
              
              <div style="display: inline-block; padding: 20px 40px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); border-radius: 12px; margin: 20px 0;">
                <p style="margin: 0; font-size: 48px; font-weight: 700; color: #ffffff; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                  ${otp}
                </p>
              </div>

              <p style="margin: 20px 0 0 0; font-size: 14px; color: #6b7280;">
                This OTP is valid for <strong>${this.OTP_EXPIRY_MINUTES} minutes</strong>
              </p>
              <p style="margin: 5px 0 0 0; font-size: 13px; color: #9ca3af;">
                Expires at: ${expiresAt.toLocaleString('en-US', { 
                  month: 'short', 
                  day: 'numeric', 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </p>
            </td>
          </tr>

          <!-- Instructions -->
          <tr>
            <td style="padding: 0 30px 30px 30px;">
              <div style="padding: 20px; background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 8px;">
                <p style="margin: 0 0 10px 0; font-size: 14px; font-weight: 600; color: #991b1b;">
                  ⚠️ Security Notice
                </p>
                <p style="margin: 0; font-size: 13px; color: #7f1d1d; line-height: 1.6;">
                  • Do not share this OTP with anyone<br>
                  • This OTP can only be used once<br>
                  • If you didn't request this, please ignore this email<br>
                  • Any of the 5 admin OTPs can unlock restricted mode
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 30px; background-color: #f9fafb; text-align: center; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0; font-size: 14px; color: #6b7280;">
                This is an automated security email from your monitoring system
              </p>
              <p style="margin: 10px 0 0 0; font-size: 12px; color: #9ca3af;">
                Generated on ${new Date().toLocaleString('en-US', { 
                  month: 'long', 
                  day: 'numeric', 
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    `;

    // Use the same email service that sends reports
    const transporter = (emailService as any).transporter;
    
    if (!transporter) {
      // Initialize if not already done
      await (emailService as any).initializeTransporter();
    }

    try {
      const info = await (emailService as any).transporter.sendMail({
        from: `"Monitoring System Security" <${process.env.SMTP_EMAIL}>`,
        to: email,
        subject: '🔐 Restricted Mode OTP - Monitoring System',
        html: htmlContent,
      });

      logger.info(`✅ OTP email sent successfully. Message ID: ${info.messageId}`);
    } catch (error) {
      logger.error('❌ Failed to send OTP email:', error);
      throw new Error('Failed to send OTP email. Please check SMTP configuration.');
    }
  }

  /**
   * Verify OTP for any admin email
   */
  verifyOTP(otp: string): boolean {
    logger.info(`🔍 Verifying OTP: ${otp.substring(0, 2)}****`);

    // Check if OTP exists for any admin
    for (const [email, record] of this.otpStore.entries()) {
      if (record.otp === otp) {
        // Check if expired
        if (new Date() > record.expiresAt) {
          logger.warn(`⏰ OTP expired for: ${email.substring(0, 3)}***`);
          this.otpStore.delete(email);
          return false;
        }

        // Valid OTP - clear all OTPs
        logger.info(`✅ Valid OTP verified for: ${email.substring(0, 3)}***`);
        this.otpStore.clear();
        return true;
      }
    }

    logger.warn('❌ Invalid OTP provided');
    return false;
  }

  /**
   * Clear all OTPs (for cleanup)
   */
  clearAllOTPs(): void {
    this.otpStore.clear();
    logger.info('🧹 All OTPs cleared');
  }

  /**
   * Get OTP status (for debugging)
   */
  getOTPStatus(): { count: number; emails: string[] } {
    const emails = Array.from(this.otpStore.keys()).map(email => 
      email.substring(0, 3) + '***'
    );
    return {
      count: this.otpStore.size,
      emails,
    };
  }
}

export const otpService = new OTPService();
