-- Drop existing notifications table
DROP TABLE IF EXISTS notifications;

-- Create new announcements table (simple, no user_id)
CREATE TABLE announcements (
    announcement_id INT PRIMARY KEY AUTO_INCREMENT,
    message VARCHAR(500) NOT NULL,
    announcement_type ENUM('SYSTEM', 'REMINDER', 'FINE_NOTICE') DEFAULT 'SYSTEM',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for faster queries
CREATE INDEX idx_created_at ON announcements(created_at DESC);
