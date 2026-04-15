import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { AnalysisData, Message } from '../../../models/analysis.models';

@Injectable()
export class AnalysisStateService {
  private isConnectedSubject = new BehaviorSubject<boolean>(false);
  private messagesSubject = new BehaviorSubject<Message[]>([]);
  private analysisDataSubject = new BehaviorSubject<AnalysisData | null>(null);

  isConnected$ = this.isConnectedSubject.asObservable();
  messages$ = this.messagesSubject.asObservable();
  analysisData$ = this.analysisDataSubject.asObservable();

  connect(_repoUrl: string, _token: string): void {
    this.isConnectedSubject.next(true);
    this.messagesSubject.next([
      {
        role: 'assistant',
        content:
          "Repository connected successfully! I'm ready to analyze your codebase. Ask me anything about your system's business logic, flows, or architecture.",
      },
    ]);
  }

  sendMessage(text: string): void {
    const current = this.messagesSubject.getValue();
    this.messagesSubject.next([...current, { role: 'user', content: text }]);

    setTimeout(() => {
      const response = this.generateMockResponse(text);
      const updated = this.messagesSubject.getValue();
      this.messagesSubject.next([
        ...updated,
        { role: 'assistant', content: response.text },
      ]);
      this.analysisDataSubject.next(response.data);
    }, 1000);
  }

  private generateMockResponse(message: string): {
    text: string;
    data: AnalysisData | null;
  } {
    const lower = message.toLowerCase();

    if (lower.includes('reservation') || lower.includes('booking')) {
      return {
        text: "I've analyzed the reservation flow in your system. Here's a detailed breakdown of how the booking process works from frontend to backend.",
        data: {
          steps: [
            {
              number: 1,
              title: 'User Initiates Booking',
              frontendComponent: 'BookingForm.tsx',
              userAction: 'Fills out reservation form with date, time, and party size',
              apiEndpoint: 'POST /api/reservations',
              backendMethod: 'ReservationController.create()',
            },
            {
              number: 2,
              title: 'Validate Availability',
              frontendComponent: 'DatePicker.tsx',
              userAction: 'Selects preferred date and time',
              apiEndpoint: 'GET /api/availability',
              backendMethod: 'AvailabilityService.checkSlots()',
            },
            {
              number: 3,
              title: 'Process Payment',
              frontendComponent: 'PaymentForm.tsx',
              userAction: 'Enters payment information',
              apiEndpoint: 'POST /api/payments',
              backendMethod: 'PaymentService.processDeposit()',
            },
            {
              number: 4,
              title: 'Confirm Reservation',
              frontendComponent: 'ConfirmationPage.tsx',
              userAction: 'Reviews booking details',
              apiEndpoint: 'PUT /api/reservations/:id/confirm',
              backendMethod: 'ReservationService.confirmBooking()',
            },
            {
              number: 5,
              title: 'Send Confirmation',
              frontendComponent: 'EmailConfirmation.tsx',
              userAction: 'Receives confirmation email',
              apiEndpoint: 'POST /api/notifications/email',
              backendMethod: 'NotificationService.sendEmail()',
            },
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
              snippet: `export function BookingForm() {
  const handleSubmit = async (data) => {
    const response = await fetch('/api/reservations', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response.json();
  };
}`,
            },
            {
              file: 'src/api/controllers/ReservationController.ts',
              snippet: `class ReservationController {
  async create(req: Request, res: Response) {
    const availability = await this.checkAvailability(req.body);
    if (!availability) {
      return res.status(400).json({ error: 'No slots available' });
    }
  }
}`,
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
            {
              number: 1,
              title: 'User Login',
              frontendComponent: 'LoginForm.tsx',
              userAction: 'Enters email and password',
              apiEndpoint: 'POST /api/auth/login',
              backendMethod: 'AuthController.login()',
            },
            {
              number: 2,
              title: 'Validate Credentials',
              frontendComponent: 'LoginForm.tsx',
              userAction: 'Submits login form',
              apiEndpoint: 'POST /api/auth/validate',
              backendMethod: 'AuthService.validateUser()',
            },
            {
              number: 3,
              title: 'Generate JWT Token',
              frontendComponent: 'AuthContext.tsx',
              userAction: 'Receives authentication token',
              apiEndpoint: 'POST /api/auth/token',
              backendMethod: 'TokenService.generateJWT()',
            },
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
              snippet: `export function LoginForm() {
  const { login } = useAuth();
  const handleSubmit = async (e) => {
    const { token } = await login(email, password);
    localStorage.setItem('authToken', token);
    navigate('/dashboard');
  };
}`,
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
