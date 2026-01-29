
# -----------------------------------------------------------------------------
# 勤怠修正フロー (Checkout後)
# -----------------------------------------------------------------------------

class AttendanceStepBaseView(LoginRequiredMixin, View):
    """勤怠修正フローの基底クラス"""
    def get_application(self, application_id):
        # 自分の応募でかつチェックアウト済みのものを取得（チェックアウト直後なのでleaving_atはあるはず）
        return get_object_or_404(JobApplication, id=application_id, worker=self.request.user)

    def get_session_data(self, application_id):
        key = f'correction_data_{application_id}'
        return self.request.session.get(key, {})

    def update_session_data(self, application_id, data):
        key = f'correction_data_{application_id}'
        current_data = self.request.session.get(key, {})
        current_data.update(data)
        self.request.session[key] = current_data
        self.request.session.modified = True

class AttendanceStep1CheckView(AttendanceStepBaseView):
    """Step 1: 就業時間は予定通りでしたか？"""
    template_name = 'jobs/attendance_step1.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})

    def post(self, request, application_id):
        action = request.POST.get('action')
        if action == 'as_scheduled':
            # 予定通り -> 完了画面(qr_success相当)へ
            # 必要であればここでAttendanceCorrectionを作る必要はないが、完了画面を表示する
            application = self.get_application(application_id)
            return render(request, 'jobs/qr_success.html', {
                'app': application, 
                'is_checkin': False
            })
        elif action == 'changed':
            # 変更があった -> Step 2へ
            return redirect('attendance_step2', application_id=application_id)
        return redirect('attendance_step1', application_id=application_id)

class AttendanceStep2GuideView(AttendanceStepBaseView):
    """Step 2: 修正依頼の流れ (ガイド画面)"""
    template_name = 'jobs/attendance_step2.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})
        
    def post(self, request, application_id):
        return redirect('attendance_step3', application_id=application_id)

class AttendanceStep3TimeView(AttendanceStepBaseView):
    """Step 3: 業務開始・終了日時の入力"""
    template_name = 'jobs/attendance_step3.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        
        # 初期値は実際の打刻時間、なければ予定時間
        initial = {
            'attendance_date': session_data.get('attendance_date') or application.attendance_at.strftime('%Y-%m-%d') if application.attendance_at else timezone.localdate().strftime('%Y-%m-%d'),
            'attendance_time': session_data.get('attendance_time') or (application.attendance_at.strftime('%H:%M') if application.attendance_at else ''),
            'leaving_date': session_data.get('leaving_date') or application.leaving_at.strftime('%Y-%m-%d') if application.leaving_at else timezone.localdate().strftime('%Y-%m-%d'),
            'leaving_time': session_data.get('leaving_time') or (application.leaving_at.strftime('%H:%M') if application.leaving_at else ''),
        }
        return render(request, self.template_name, {'application': application, 'initial': initial})

    def post(self, request, application_id):
        # フォームデータの保存
        data = {
            'attendance_date': request.POST.get('attendance_date'),
            'attendance_time': request.POST.get('attendance_time'),
            'leaving_date': request.POST.get('leaving_date'),
            'leaving_time': request.POST.get('leaving_time'),
        }
        self.update_session_data(application_id, data)
        return redirect('attendance_step4', application_id=application_id)

class AttendanceStep4BreakView(AttendanceStepBaseView):
    """Step 4: 休憩時間の入力"""
    template_name = 'jobs/attendance_step4.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        initial_break = session_data.get('break_time', application.job_posting.break_duration)
        return render(request, self.template_name, {'application': application, 'break_time': initial_break})

    def post(self, request, application_id):
        break_time = request.POST.get('break_time')
        self.update_session_data(application_id, {'break_time': break_time})
        
        # 遅刻判定
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        
        # 入力された開始日時を構築
        try:
            att_date = session_data.get('attendance_date')
            att_time = session_data.get('attendance_time')
            input_start_dt = datetime.strptime(f"{att_date} {att_time}", '%Y-%m-%d %H:%M')
            input_start_dt = timezone.make_aware(input_start_dt)
            
            # 予定開始日時
            scheduled_start_dt = timezone.make_aware(datetime.combine(application.job_posting.work_date, application.job_posting.start_time))
            
            # 1分以上の遅刻とみなすか
            if input_start_dt > scheduled_start_dt:
                return redirect('attendance_step5', application_id=application_id)
            else:
                return redirect('attendance_step6', application_id=application_id)

        except ValueError:
            # 日時パースエラー等の場合はとりあえず進むか戻るか...ここではStep6へ
            return redirect('attendance_step6', application_id=application_id)


class AttendanceStep5LatenessView(AttendanceStepBaseView):
    """Step 5: 遅刻理由の入力 (遅刻時のみ)"""
    template_name = 'jobs/attendance_step5.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})

    def post(self, request, application_id):
        # 理由の保存
        reason = request.POST.get('lateness_reason_detail') # テキストエリア
        # 選択肢もあれば保存するが、今回はテキストエリアメインの画面
        self.update_session_data(application_id, {'lateness_reason_detail': reason})
        return redirect('attendance_step6', application_id=application_id)

class AttendanceStep6ConfirmView(AttendanceStepBaseView):
    """Step 6: 最終確認"""
    template_name = 'jobs/attendance_step6.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        return render(request, self.template_name, {'application': application, 'data': session_data})

    def post(self, request, application_id):
        # DB保存
        application = self.get_application(application_id)
        session_data = self.get_session_data(application_id)
        
        att_str = f"{session_data.get('attendance_date')} {session_data.get('attendance_time')}"
        leave_str = f"{session_data.get('leaving_date')} {session_data.get('leaving_time')}"
        
        correction_att = timezone.make_aware(datetime.strptime(att_str, '%Y-%m-%d %H:%M'))
        correction_leave = timezone.make_aware(datetime.strptime(leave_str, '%Y-%m-%d %H:%M'))
        
        AttendanceCorrection.objects.create(
            application=application,
            correction_attendance_at=correction_att,
            correction_leaving_at=correction_leave,
            correction_break_time=int(session_data.get('break_time', 0)),
            lateness_reason_detail=session_data.get('lateness_reason_detail', ''),
            status='pending'
        )
        
        # セッションクリア
        key = f'correction_data_{application_id}'
        if key in request.session:
            del request.session[key]
            
        return redirect('attendance_step7', application_id=application_id)

class AttendanceStep7FinishView(AttendanceStepBaseView):
    """Step 7: 完了画面"""
    template_name = 'jobs/attendance_step7.html'

    def get(self, request, application_id):
        application = self.get_application(application_id)
        return render(request, self.template_name, {'application': application})
