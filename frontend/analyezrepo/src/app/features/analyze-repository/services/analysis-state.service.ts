import { Injectable, signal } from '@angular/core';
import { AnalysisData, Message, Repository } from '../../../models/analysis.models';

@Injectable()
export class AnalysisStateService {
  readonly isConnected = signal(false);
  readonly messages = signal<Message[]>([]);
  readonly analysisData = signal<AnalysisData | null>(null);

  connect(repo: Repository): void {
    this.isConnected.set(true);
    this.messages.set([
      {
        role: 'assistant',
        content: `Connected to ${repo.name}! I'm ready to analyze your codebase. Ask me anything about your system's business logic, flows, or architecture.`,
      },
    ]);
    this.analysisData.set(null);
  }

  reset(): void {
    this.isConnected.set(false);
    this.messages.set([]);
    this.analysisData.set(null);
  }

  sendMessage(text: string): void {
    this.messages.update(msgs => [...msgs, { role: 'user', content: text }]);

    setTimeout(() => {
      const response = this.generateMockResponse(text);
      this.messages.update(msgs => [...msgs, { role: 'assistant', content: response.text }]);
      this.analysisData.set(response.data);
    }, 1000);
  }

  private generateMockResponse(message: string): { text: string; data: AnalysisData | null } {
    const lower = message.toLowerCase();

    if (lower.includes('reservation') || lower.includes('booking')) {
      return {
        text: "I've analyzed the reservation flow in your system. Here's a detailed breakdown of how the booking process works from frontend to backend.",
        data: {
          steps: [
            { number: 1, title: 'User Initiates Booking',  frontendComponent: 'BookingForm.tsx',      userAction: 'Fills out reservation form',             apiEndpoint: 'POST /api/reservations',            backendMethod: 'ReservationController.create()' },
            { number: 2, title: 'Validate Availability',   frontendComponent: 'DatePicker.tsx',        userAction: 'Selects preferred date and time',        apiEndpoint: 'GET /api/availability',             backendMethod: 'AvailabilityService.checkSlots()' },
            { number: 3, title: 'Process Payment',         frontendComponent: 'PaymentForm.tsx',       userAction: 'Enters payment information',             apiEndpoint: 'POST /api/payments',                backendMethod: 'PaymentService.processDeposit()' },
            { number: 4, title: 'Confirm Reservation',     frontendComponent: 'ConfirmationPage.tsx',  userAction: 'Reviews booking details',                apiEndpoint: 'PUT /api/reservations/:id/confirm', backendMethod: 'ReservationService.confirmBooking()' },
            { number: 5, title: 'Send Confirmation',       frontendComponent: 'EmailConfirmation.tsx', userAction: 'Receives confirmation email',            apiEndpoint: 'POST /api/notifications/email',     backendMethod: 'NotificationService.sendEmail()' },
          ],
          mermaidCode: `graph TD
    A[User Opens Booking Page] --> B[Fill Reservation Form]
    B --> C[Select Date & Time]
    C --> D{Check Availability}
    D -->|Available| E[Enter Payment Info]
    D -->|Not Available| C
    E --> F[Process Payment]
    F --> G{Payment Success?}
    G -->|Yes| H[Create Reservation]
    G -->|No| E
    H --> I[Send Confirmation Email]
    I --> J[Display Confirmation Page]
    style A fill:#6366F1
    style J fill:#10B981
    style D fill:#F59E0B
    style G fill:#F59E0B`,
          codeReferences: [
            {
              file: 'src/components/BookingForm.tsx',
              snippet: `export function BookingForm() {\n  const handleSubmit = async (data) => {\n    const response = await fetch('/api/reservations', {\n      method: 'POST',\n      body: JSON.stringify(data)\n    });\n    return response.json();\n  };\n}`,
            },
            {
              file: 'src/api/controllers/ReservationController.ts',
              snippet: `class ReservationController {\n  async create(req: Request, res: Response) {\n    const availability = await this.checkAvailability(req.body);\n    if (!availability) {\n      return res.status(400).json({ error: 'No slots available' });\n    }\n  }\n}`,
            },
          ],
        },
      };
    }

    if (lower.includes('auth') || lower.includes('login')) {
      return {
        text: "I've mapped out the authentication flow in your application.",
        data: {
          steps: [
            { number: 1, title: 'User Login',          frontendComponent: 'LoginForm.tsx',  userAction: 'Enters email and password',          apiEndpoint: 'POST /api/auth/login',     backendMethod: 'AuthController.login()' },
            { number: 2, title: 'Validate Credentials', frontendComponent: 'LoginForm.tsx',  userAction: 'Submits login form',                 apiEndpoint: 'POST /api/auth/validate',  backendMethod: 'AuthService.validateUser()' },
            { number: 3, title: 'Generate JWT Token',   frontendComponent: 'AuthContext.tsx', userAction: 'Receives authentication token',     apiEndpoint: 'POST /api/auth/token',     backendMethod: 'TokenService.generateJWT()' },
          ],
          mermaidCode: `graph TD
    A[User Opens Login Page] --> B[Enter Credentials]
    B --> C[Submit Form]
    C --> D{Validate Credentials}
    D -->|Invalid| E[Show Error]
    E --> B
    D -->|Valid| F[Generate JWT Token]
    F --> G[Create Session]
    G --> H[Redirect to Dashboard]
    style A fill:#6366F1
    style H fill:#10B981
    style D fill:#F59E0B
    style E fill:#EF4444`,
          codeReferences: [
            {
              file: 'src/components/LoginForm.tsx',
              snippet: `export function LoginForm() {\n  const { login } = useAuth();\n  const handleSubmit = async (e) => {\n    const { token } = await login(email, password);\n    localStorage.setItem('authToken', token);\n    navigate('/dashboard');\n  };\n}`,
            },
          ],
        },
      };
    }

    return {
      text: "I understand you're asking about your system. Could you be more specific? For example:\n\n• How does the reservation flow work?\n• Explain the authentication process\n• How does payment processing work?",
      data: null,
    };
  }
}
